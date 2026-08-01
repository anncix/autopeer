package api

import (
	"strings"
	"sync"
	"time"

	"dn42-autopeer-node/internal/runner"
)

// maxFlapEvents caps the in-memory ring buffer of flap events kept per agent process. Older events
// are dropped once the cap is reached. This is a best-effort, recent-history view — agents restart
// lose history, which is acceptable for a P2 observability feature (the operator still has BIRD
// logs for full forensics).
// maxFlapEvents 限制每個 agent 進程保留的抖動事件環形緩衝上限。達上限後丟棄最舊事件。
// 這是盡力而為的近期歷史視圖——agent 重啟會丟失歷史,對 P2 可觀測性功能可接受
// (完整取證操作者仍有 BIRD 日誌)。
const maxFlapEvents = 200

// FlapEvent records one BGP protocol state transition detected by polling birdc.
// FlapEvent 記錄一次透過輪詢 birdc 偵測到的 BGP 協定狀態轉換。
type FlapEvent struct {
	Protocol string `json:"protocol"`       // BIRD protocol name (e.g. DN42_0090_a1b2)
	From     string `json:"from"`            // previous state (up/start/down), "" if newly seen
	To       string `json:"to"`              // current state
	Time     string `json:"time"`            // RFC3339 timestamp of detection
}

// FlapCheckResponse is returned by the flap.check command: the events observed on this poll plus
// the current BGP protocol states (so the UI can show live state alongside history).
// FlapCheckResponse 由 flap.check 命令回傳:本次輪詢觀察到的事件,加上當前 BGP 協定狀態
// (讓 UI 能同時顯示即時狀態與歷史)。
type FlapCheckResponse struct {
	OK         bool              `json:"ok"`
	Error      string            `json:"error,omitempty"`
	NewEvents  []FlapEvent       `json:"new_events"`          // transitions seen on this poll
	States     map[string]string `json:"states"`              // protocol -> current state
	EventCount int               `json:"event_count"`         // total events in buffer
	RawOutput  string            `json:"raw_output,omitempty"` // last birdc output (for debugging)
}

// FlapEventsResponse is returned by the flap.events command: the full buffered history.
// FlapEventsResponse 由 flap.events 命令回傳:完整緩衝歷史。
type FlapEventsResponse struct {
	OK     bool        `json:"ok"`
	Error  string      `json:"error,omitempty"`
	Events []FlapEvent `json:"events"`
}

// flapState holds the cross-poll state for BGP flap detection. It lives on *Server (single long-lived
// instance), protected by a mutex. Runner is stateless (value receiver), so this is the natural home
// for "remember the last birdc show protocols snapshot".
// flapState 持有 BGP 抖動偵測的跨輪詢狀態。它存活於 *Server(單一長駐實例),以 mutex 保護。
// Runner 無狀態(值接收者),故「記住上一次 birdc show protocols 快照」自然落於此處。
type flapState struct {
	mu     sync.Mutex
	last   map[string]string // protocol -> last observed state
	events []FlapEvent       // ring buffer (newest appended, oldest dropped at cap)
}

func newFlapState() *flapState {
	return &flapState{last: make(map[string]string)}
}

// parseBirdProtocols extracts BGP protocol name -> state from `birdc show protocols` output.
// Output shape (BIRD2):
//
//	Name       Proto      Table      State  Since         Info
//	device1    Device     ---        up     14:23:01.234
//	DN42_xxx   BGP        ---        up     14:25:33.123  Established
//
// Only BGP rows are tracked (device/kernel/static don't flap meaningfully). The State column
// (index 3) is the canonical up/start/down; the Info column carries the BGP sub-state
// (Established/Active/Connect) but we key on State for transition detection.
// parseBirdProtocols 從 `birdc show protocols` 輸出提取 BGP 協定名稱 -> 狀態。
// 僅追蹤 BGP 列(device/kernel/static 無有意義的抖動)。State 欄(索引 3)為正規 up/start/down;
// Info 欄帶 BGP 子狀態(Established/Active/Connect),但轉換偵測以 State 為準。
func parseBirdProtocols(output string) map[string]string {
	states := make(map[string]string)
	for _, line := range strings.Split(output, "\n") {
		fields := strings.Fields(line)
		if len(fields) < 4 {
			continue
		}
		name, proto, state := fields[0], fields[1], fields[3]
		if proto != "BGP" {
			continue
		}
		// Skip the header row (Name/Proto/Table/State...). Its proto field would be "Proto", not "BGP",
		// so the BGP filter already excludes it; keep this guard for robustness against locale variants.
		if name == "Name" {
			continue
		}
		states[name] = state
	}
	return states
}

// check polls birdc, compares BGP states against the last snapshot, records transitions, and returns
// the new events + current states. Called by the backend on demand (admin opens the flap page, or a
// periodic task invokes flap.check). The first poll for a protocol records a synthetic "new" event
// with From="" so the UI can show initial state.
// check 輪詢 birdc,將 BGP 狀態與上次快照對比,記錄轉換,並回傳新事件與當前狀態。由後端按需呼叫
// (管理員開啟抖動頁面,或週期任務觸發 flap.check)。某 protocol 首次被觀察到時記錄一個 From=""
// 的「新增」事件,讓 UI 能顯示初始狀態。
func (f *flapState) check(r runner.Runner) FlapCheckResponse {
	res := r.BirdProtocols()
	if !res.OK {
		return FlapCheckResponse{OK: false, Error: "birdc show protocols failed", RawOutput: res.Output}
	}
	current := parseBirdProtocols(res.Output)

	f.mu.Lock()
	defer f.mu.Unlock()

	var newEvents []FlapEvent
	now := time.Now().UTC().Format(time.RFC3339)

	// Detect transitions: a protocol's state changed, or it appeared/disappeared.
	// 偵測轉換:某 protocol 狀態改變,或出現/消失。
	for name, state := range current {
		prev, existed := f.last[name]
		if !existed {
			// Newly observed protocol — record an arrival event (From empty).
			// 新觀察到的 protocol——記錄到達事件(From 為空)。
			ev := FlapEvent{Protocol: name, From: "", To: state, Time: now}
			f.appendLocked(ev)
			newEvents = append(newEvents, ev)
		} else if prev != state {
			ev := FlapEvent{Protocol: name, From: prev, To: state, Time: now}
			f.appendLocked(ev)
			newEvents = append(newEvents, ev)
		}
	}
	// Protocols that vanished since last poll (e.g. removed from BIRD) — record a departure.
	// 自上次輪詢後消失的 protocol(例如自 BIRD 移除)——記錄離開事件。
	for name, prev := range f.last {
		if _, stillThere := current[name]; !stillThere {
			ev := FlapEvent{Protocol: name, From: prev, To: "gone", Time: now}
			f.appendLocked(ev)
			newEvents = append(newEvents, ev)
		}
	}

	f.last = current

	return FlapCheckResponse{
		OK:         true,
		NewEvents:  newEvents,
		States:     current,
		EventCount: len(f.events),
	}
}

// appendLocked appends an event and trims the buffer to maxFlapEvents. Caller must hold f.mu.
// appendLocked 附加事件並將緩衝修剪至 maxFlapEvents。呼叫者須持有 f.mu。
func (f *flapState) appendLocked(ev FlapEvent) {
	f.events = append(f.events, ev)
	if len(f.events) > maxFlapEvents {
		// Drop the oldest: shift the slice. A ring buffer would avoid the copy, but at cap 200 the
		// copy cost is negligible and the simpler slice keeps JSON marshalling trivial.
		// 丟棄最舊:平移切片。環形緩衝可避免複製,但上限 200 時複製成本可忽略,且簡單切片讓
		// JSON 序列化更直觀。
		f.events = f.events[len(f.events)-maxFlapEvents:]
	}
}

// history returns a copy of the buffered history (newest last). Safe for concurrent callers.
// history 回傳緩衝歷史的副本(最新在最後)。對並發呼叫者安全。
func (f *flapState) history() FlapEventsResponse {
	f.mu.Lock()
	defer f.mu.Unlock()
	// Copy so the caller gets a stable snapshot independent of future appends.
	// 複製一份,讓呼叫者取得獨立於後續附加的穩定快照。
	out := make([]FlapEvent, len(f.events))
	copy(out, f.events)
	return FlapEventsResponse{OK: true, Events: out}
}
