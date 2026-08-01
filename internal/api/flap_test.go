package api

import (
	"strings"
	"testing"
)

// TestParseBirdProtocols verifies the BIRD2 `show protocols` parser extracts only BGP rows and
// ignores the header / device / kernel / static protocols. This is the foundation of flap
// detection — a misparse here would either miss real flaps or fire false positives on non-BGP rows.
// 驗證 BIRD2 `show protocols` 解析器只提取 BGP 列,並忽略表頭 / device / kernel / static 協定。
// 此為抖動偵測的基礎——解析錯誤會導致漏報真實抖動或在非 BGP 列上誤報。
func TestParseBirdProtocols(t *testing.T) {
	output := `Name       Proto      Table      State  Since         Info
device1    Device     ---        up     14:23:01.234
kernel1    Kernel     master4    up     14:23:01.234
static1    Static     ---        up     14:23:01.234
DN42_0090  BGP        ---        up     14:25:33.123  Established
DN42_1234  BGP        ---        start  14:25:34.456  Active
DN42_5678  BGP        ---        down   14:25:35.789
`
	states := parseBirdProtocols(output)

	if len(states) != 3 {
		t.Fatalf("expected 3 BGP protocols, got %d: %v", len(states), states)
	}
	cases := map[string]string{
		"DN42_0090": "up",
		"DN42_1234": "start",
		"DN42_5678": "down",
	}
	for name, want := range cases {
		if got := states[name]; got != want {
			t.Errorf("state for %s: want %q, got %q", name, want, got)
		}
	}
	// Header row's "Proto" must not leak through as a BGP entry.
	if _, ok := states["Name"]; ok {
		t.Errorf("header row leaked into BGP states: %v", states)
	}
	// Non-BGP protocols must be absent.
	for _, bad := range []string{"device1", "kernel1", "static1"} {
		if _, ok := states[bad]; ok {
			t.Errorf("non-BGP protocol %q should be ignored, got state", bad)
		}
	}
}

// TestParseBirdProtocolsEmptyInput confirms the parser tolerates empty / whitespace-only output
// (e.g. birdc not configured, no peers) without panicking, returning an empty map.
// 確認解析器容忍空 / 僅空白輸出(例如 birdc 未設定、無 peer)不會 panic,回傳空 map。
func TestParseBirdProtocolsEmptyInput(t *testing.T) {
	for _, input := range []string{"", "\n\n", "Name       Proto      Table      State  Since         Info\n"} {
		states := parseBirdProtocols(input)
		if len(states) != 0 {
			t.Errorf("expected empty states for input %q, got %v", input, states)
		}
	}
}

// TestFlapStateRingBufferTrims verifies the ring buffer caps at maxFlapEvents and drops the oldest
// entries. Without this cap a long-running agent would accumulate unbounded memory; the cap keeps
// the recent-history view bounded while the operator still has BIRD logs for full forensics.
// 驗證環形緩衝在 maxFlapEvents 上限處截斷並丟棄最舊項。無此上限,長駐 agent 會累積無界記憶體;
// 上限保持近期歷史視圖有界,操作者仍有 BIRD 日誌供完整取證。
func TestFlapStateRingBufferTrims(t *testing.T) {
	f := newFlapState()
	// Push maxFlapEvents + 50 — the buffer should keep only the last maxFlapEvents.
	total := maxFlapEvents + 50
	for i := 0; i < total; i++ {
		f.mu.Lock()
		f.appendLocked(FlapEvent{
			Protocol: "DN42_x",
			From:     "up",
			To:       "down",
			Time:     "2026-08-01T00:00:00Z",
		})
		f.mu.Unlock()
	}
	hist := f.history()
	if !hist.OK {
		t.Fatalf("history() returned OK=false: %+v", hist)
	}
	if len(hist.Events) != maxFlapEvents {
		t.Fatalf("expected %d buffered events, got %d", maxFlapEvents, len(hist.Events))
	}
}

// TestFlapStateHistoryReturnsCopy verifies history() returns a stable copy: appending to the
// buffer after the call must not mutate the previously-returned slice. This matters because the
// admin flap page calls flap.events then renders while another flap.check could append.
// 驗證 history() 回傳穩定副本:呼叫後再附加進緩衝不應變動先前回傳的切片。這很重要,因為
// 管理員抖動頁面呼叫 flap.events 後渲染時,另一個 flap.check 可能同時附加。
func TestFlapStateHistoryReturnsCopy(t *testing.T) {
	f := newFlapState()
	f.mu.Lock()
	f.appendLocked(FlapEvent{Protocol: "DN42_a", From: "up", To: "down", Time: "t1"})
	f.mu.Unlock()

	snap1 := f.history()
	if len(snap1.Events) != 1 {
		t.Fatalf("snap1 expected 1 event, got %d", len(snap1.Events))
	}

	// Append more events after the snapshot.
	f.mu.Lock()
	f.appendLocked(FlapEvent{Protocol: "DN42_b", From: "down", To: "up", Time: "t2"})
	f.mu.Unlock()

	snap2 := f.history()
	if len(snap2.Events) != 2 {
		t.Fatalf("snap2 expected 2 events, got %d", len(snap2.Events))
	}
	// snap1 must be unchanged — it's a copy, not a view.
	if len(snap1.Events) != 1 {
		t.Errorf("snap1 was mutated after later append: now %d events", len(snap1.Events))
	}
}

// TestFlapStateHistoryEmpty verifies a freshly-created flapState returns OK with an empty (not nil)
// events slice, so JSON marshalling yields `[]` not `null`. The frontend expects an array.
// 驗證新建 flapState 回傳 OK 且 events 為空(非 nil)切片,讓 JSON 序列化產生 [] 而非 null。
// 前端期望陣列。
func TestFlapStateHistoryEmpty(t *testing.T) {
	f := newFlapState()
	hist := f.history()
	if !hist.OK {
		t.Fatalf("expected OK=true, got false")
	}
	if hist.Events == nil {
		t.Errorf("expected non-nil empty slice, got nil (would marshal to null)")
	}
	if len(hist.Events) != 0 {
		t.Errorf("expected 0 events, got %d", len(hist.Events))
	}
}

// TestNewFlapStateInitialised verifies newFlapState() initialises the last map (so check() can
// write to it without a nil-map panic) and starts with no events.
// 驗證 newFlapState() 初始化 last map(讓 check() 可寫入而不會 nil-map panic),且初始無事件。
func TestNewFlapStateInitialised(t *testing.T) {
	f := newFlapState()
	if f.last == nil {
		t.Fatal("last map is nil — check() would panic on write")
	}
	if len(f.last) != 0 {
		t.Errorf("expected empty last map, got %d entries", len(f.last))
	}
	if f.events != nil && len(f.events) != 0 {
		t.Errorf("expected no buffered events, got %d", len(f.events))
	}
}

// TestParseBirdProtocolsMalformedRows verifies the parser skips short rows (fewer than 4 fields)
// rather than panicking on index-out-of-range. BIRD output is generally well-formed but a stray
// blank line or truncated row should never crash the agent.
// 驗證解析器跳過短列(少於 4 欄)而非 panic 於索引越界。BIRD 輸出通常格式良好,但偶發空白行或
// 截斷列絕不應讓 agent 當機。
func TestParseBirdProtocolsMalformedRows(t *testing.T) {
	output := strings.Join([]string{
		"Name       Proto      Table      State  Since         Info",
		"short",                       // 1 field — skip
		"two fields",                  // 2 fields — skip
		"three fields here",           // 3 fields — skip
		"DN42_0090  BGP        ---        up     14:25:33.123  Established", // valid
		"",                                                            // blank — skip
	}, "\n")
	states := parseBirdProtocols(output)
	if len(states) != 1 {
		t.Fatalf("expected 1 BGP protocol, got %d: %v", len(states), states)
	}
	if states["DN42_0090"] != "up" {
		t.Errorf("DN42_0090 state: want up, got %q", states["DN42_0090"])
	}
}
