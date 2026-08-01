# AutoPeer

[English](README.md) | **繁體中文**

**dn42 自助對等平台與公開 Looking Glass。**

AutoPeer 自動化跨分散式 dn42 節點建立 BGP 對等:使用者驗證 ASN 擁有權、選擇節點、提交
WireGuard 公鑰,即可在數分鐘內取得可直接使用的 WireGuard + BIRD 設定——無需手動設定路由器。可
透過 Web UI、Telegram bot 或 REST API(`/api/v1`)管理一切。

> 版本:**0.0.2** · Python 3.11+ · Go 1.21+ · MIT 授權

---

## 目錄

- [運行](#運行)
- [結構](#結構)
- [API](#api)
- [更新(變更紀錄)](#更新變更紀錄)
- [安全](#安全)

---

## 運行

### 前置需求

- Python 3.11+、Go 1.21+
- 公開 HTTPS 網域(正式環境)或 `--allow-http`(本地測試)
- 每台節點路由器上的 WireGuard + BIRD

### Backend 設定

```bash
git clone https://github.com/anncix/autopeer.git
cd autopeer

cp .env.example .env          # 再編輯 .env(見下方)
python3 -m pip install -r requirements.txt
python3 start.py
```

`.env`(必要密鑰——除非 `ALLOW_INSECURE_DEFAULTS=1`,否則 backend 拒絕以佔位值啟動):

```bash
DOMAIN=your.domain.com
LOCAL_ASN=4242420000
SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
TELEGRAM_BACKEND_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 選用
TELEGRAM_BOT_TOKEN=            # 來自 BotFather;留空即停用 bot
FINDNOC_API_TOKEN=             # 選用的 bot FindNOC 快速登入
ALLOW_INSECURE_DEFAULTS=0      # 僅本地測試時設為 1
```

將 Kioubit 簽章公鑰置於 `app/keys/public_key.pem`(ASN 擁有權驗證)。

### Node service 設定(每台路由器)

```bash
cd cmd/node
go build -o node .
cd ../..

cp config.example.json config.json   # 編輯 name/token/wireguard 金鑰
./node -config ./config.json
```

`config.json`:

| 鍵 | 說明 |
|-----|-------------|
| `name` | 與 backend 紀錄相符的節點名稱 |
| `token` | WSS 連線的 Bearer token(來自 admin 節點詳情 / reset-token) |
| `backend_wss_url` | Backend WebSocket URL(`wss://host/api/nodes/ws`) |
| `wireguard_public_key` / `wireguard_private_key` | 路由器 WG 金鑰(私鑰絕不離開節點) |
| `bird_peer_dir` / `wireguard_peer_dir` | 產生的 BIRD 片段 / WG 設定目錄 |
| `deploy_reload_cmd` | 部署後重載指令(如 `birdc c`) |
| `birdc_path` / `wg_path` / `wg_quick_path` / `ping_path` / `traceroute_path` / `mtr_path` | 各執行檔路徑 |

### 啟動選項

| 旗標 | 說明 |
|------|-------------|
| `--allow-http` | 本地測試;允許非 HTTPS 的 `DOMAIN` |
| `--backend-only` | 僅啟動 FastAPI backend |
| `--bot-only` | 僅啟動 Telegram bot |
| `--host` / `--port` | 覆寫 backend 綁定位置 |

### Backend 環境變數

| 變數 | 預設 | 說明 |
|----------|---------|-------------|
| `APP_NAME` | `AutoPeer` | UI 顯示名稱 |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | 綁定位置 |
| `DOMAIN` | `127.0.0.1:8000` | 公開 HTTPS 網域 |
| `SESSION_SECRET` | *(不安全預設)* | 簽章 cookie session 密鑰 |
| `DATABASE_URL` | `sqlite:///./autopeer.db` | 資料庫 URL |
| `LOCAL_ASN` | *(空)* | 操作者 ASN——授予 admin 權限 |
| `KIOUBIT_PUBLIC_KEY_PATH` | `app/keys/public_key.pem` | Kioubit ECDSA 公鑰 |
| `TELEGRAM_BOT_TOKEN` | *(空)* | Telegram BotFather token |
| `TELEGRAM_BACKEND_SECRET` | *(不安全預設)* | bot ↔ backend 共享密鑰 |
| `FINDNOC_API_TOKEN` / `FINDNOC_API_URL` | *(空)* / `https://findnoc.ox5.cc` | 選用 FindNOC 登入 |
| `LG_RATE_LIMIT` / `LG_RATE_WINDOW_SECONDS` | `20` / `60` | 公開 LG 每 IP 速率限制 |
| `FORWARDED_IP_HEADER` | *(空)* | 受信任的客戶端 IP header(僅反向代理) |

> [!WARNING]
> Node service 以 root 執行(需寫入路由器設定並呼叫 `wg-quick`)。任何可能進入 node service
> 或路由器設定的值,都應視為安全敏感輸入。

---

## 結構

```
┌─────────────────────────────────────────────────┐
│  瀏覽器 / curl          Telegram bot             │
│  (Web UI + /api/v1)    (/api/telegram/*)         │
└──────────────────────┬──────────────────────────┘
                       │
            ┌──────────▼──────────┐
            │  控制平面            │  FastAPI + SQLAlchemy + SQLite
            │  (Python, app/)     │  · ASN 驗證(Kioubit/FindNOC)
            │                     │  · Peer 生命週期 + 設定產生
            │                     │  · REST API(/api/v1)+ Web UI
            └──────────┬──────────┘
                       │ WSS(token 驗證)
            ┌──────────▼──────────┐
            │  Node service (Go)  │  每台路由器一個
            │  cmd/node, internal/│  · WireGuard + BIRD 部署
            │                     │  · Looking-glass 指令執行
            └─────────────────────┘
```

```
autopeer/
├── app/
│   ├── api/              JSON API
│   │   ├── deps.py       require_api_user / require_api_admin(401/403 JSON)
│   │   ├── schemas.py    Pydantic 回應模型(敏感資料白名單)
│   │   ├── telegram.py   bot 專用 API(X-Backend-Secret)
│   │   └── v1/           REST CRUD API(peers, nodes, admin)
│   ├── auth/             Kioubit、FindNOC、sessions
│   ├── bot/              Telegram bot
│   ├── db/               SQLAlchemy 模型 + session
│   ├── intra/            Intra-link(iBGP/OSPF 骨幹)設定 + 部署
│   ├── lg/               Looking-glass 客戶端 + 速率限制器
│   ├── peer/             Peer 驗證、設定產生、部署
│   ├── templates/        Jinja2 HTML(admin/、macros.html、…)
│   ├── static/           CSS、JS、i18n.js
│   ├── web/              HTML 路由(pages、portal、admin、lg)
│   ├── node_ws.py        Node WebSocket 中樞
│   ├── version.py        版本(0.0.2)
│   └── main.py           FastAPI app + router 接線
├── cmd/node/             Node service 入口(Go)
├── internal/             Node service 內部(Go)
│   ├── api/              指令分派器(+ BGP 抖動偵測)
│   ├── config/           JSON 設定載入器
│   └── runner/           部署執行器
├── config.example.json   Node service 設定範本
├── start.py              啟動器(backend + bot)
├── pyproject.toml        Python 專案 + ruff 設定
└── requirements.txt
```

---

## API

AutoPeer 暴露三個 JSON API 表面。Web UI 與 `/api/v1` 共用 session-cookie 驗證;
`/api/telegram/*` 為機器對機器(共享密鑰);node WSS 通道為 token 驗證。

### `POST /lg` — Looking Glass(匿名)

查詢類型為 `{ping, traceroute, mtr, bird, route}`。帶 header `X-Requested-With: fetch` 時回傳
`{ok, output, query_type}`;否則渲染 HTML 頁面。

### `/api/v1/*` — REST CRUD API(session 驗證)

除公開節點清單外,所有 `/api/v1` 端點皆需已驗證的 session cookie(瀏覽器登入)。驗證失敗回傳
**401**(未登入)或 **403**(已登入但無權)為 JSON——兩個不同狀態碼讓客戶端能區分。驗證錯誤回傳
**400**;衝突(重複名稱、含 peer 的節點)回傳 **409**。

**Peers**(`/api/v1/peers`)——使用者範圍;僅管理自己的 peer。外來 peer id 回傳 **404**(所有權
隱藏存在性)。ASN 取自 session,故無法以他人 AS 對等。

| 方法 | 路徑 | 權限 | 說明 |
|--------|------|------|-------------|
| GET | `/api/v1/peers` | user | 列出自己的 peer |
| POST | `/api/v1/peers` | user | 建立 peer(201) |
| GET | `/api/v1/peers/{id}` | user | 取得自己的 peer |
| PATCH | `/api/v1/peers/{id}` | user | 部分更新;`status=disabled` 觸發拆除,`redeploy=true` 重新推送 |
| DELETE | `/api/v1/peers/{id}` | user | 刪除 + 盡力拆除 |

**Nodes**(`/api/v1/nodes` 公開,`/api/v1/admin/nodes` admin)

| 方法 | 路徑 | 權限 | 說明 |
|--------|------|------|-------------|
| GET | `/api/v1/nodes` | 匿名 | 列出已啟用節點(僅公開欄位) |
| GET | `/api/v1/nodes/{id}` | 匿名 | 節點詳情(公開欄位) |
| GET | `/api/v1/admin/nodes` | admin | 列出全部節點(含 token + 運行時) |
| POST | `/api/v1/admin/nodes` | admin | 建立節點(201);token 由服務端產生,回傳一次 |
| GET | `/api/v1/admin/nodes/{id}` | admin | 節點詳情(含 token) |
| PATCH | `/api/v1/admin/nodes/{id}` | admin | 部分更新 |
| DELETE | `/api/v1/admin/nodes/{id}` | admin | 刪除(仍有 peer 則 409) |
| POST | `/api/v1/admin/nodes/{id}/reset-token` | admin | 輪換 node agent token |

**Admin**(`/api/v1/admin/*`)

| 方法 | 路徑 | 說明 |
|--------|------|-------------|
| GET | `/api/v1/admin/peers` | 列出全部 peer(含 deploy_output) |
| GET | `/api/v1/admin/peers/{id}` | 任意 peer 詳情(含 deploy_output) |
| GET | `/api/v1/admin/nodes/{id}/intra-links` | 列出節點上的骨幹鏈路 |
| POST | `/api/v1/admin/nodes/{id}/intra-links` | 建立 intra-link(可雙向) |
| DELETE | `/api/v1/admin/nodes/{id}/intra-links/{link_id}` | 刪除 intra-link |
| GET | `/api/v1/admin/users` | 列出使用者(剝離 Telegram chat id / mnt JSON) |

### `/api/telegram/*` — Bot API(共享密鑰)

需 header `X-Backend-Secret` == `TELEGRAM_BACKEND_SECRET`。Peer CRUD、LG 查詢、登入
challenge/verify、FindNOC 登入、批次狀態——見 `app/api/telegram.py`。

### 敏感資料隔離

API 回應由顯式 Pydantic 白名單(`app/api/schemas.py`)構建,絕非原始 ORM 行:

- `Node.token`(agent 憑證)與 `system_status_json` **僅**出現於 admin 的 `NodeAdmin` 視圖——
  絕不出現於匿名的 `NodePublic` 清單。
- `deploy_output`(可能含節點側主機名/路徑)在屬主的 `PeerOut` 視圖中不存在,僅 admin 的
  `PeerAdmin` 視圖可見。
- `UserOut` 剝離 Telegram chat id 與 ASN 身分 maintainer JSON(PII)。
- WireGuard **私鑰絕不進入控制平面 DB**——設定使用 `{{WIREGUARD_PRIVATE_KEY}}` 佔位符,
  由 node agent 於部署時替換。

---

## 更新(變更紀錄)

### 0.0.2

- **REST CRUD API**(`/api/v1`):peers(使用者範圍、所有權強制)、nodes(公開讀 + admin CRUD)、
  intra-links、admin peer/使用者清單的完整增改刪查。複用與 HTML 路由相同的 service 函式,
  驗證與部署邏輯只維護一處。
- **權限隔離**:新增 `require_api_user` / `require_api_admin` 依賴,回傳 JSON 401/403(與 HTML
  重定向至登入的流程區隔)。跨使用者 peer 存取回傳 404 以隱藏存在性。
- **敏感資料隔離**:Pydantic 回應白名單自每個 API 回應剝離 `Node.token`、`deploy_output`(非
  admin)與 Telegram PII。
- **BGP 抖動偵測**(P2):Go node agent 輪詢 `birdc show protocols`,差分 BGP 狀態轉換
  (up/start/down)進入有界環形緩衝,並暴露 `flap.check` / `flap.events` 指令,渲染於新的
  admin 抖動頁面。
- **雙向 intra-link 建立**(P2):單次建立可選擇在遠端節點一併佈建匹配的反向鏈路,經由共享的
  `_provision_intra_link` helper。
- **漸進增強鏈路管理**(P3):鏈路頁籤以 `fetch` 對 JSON 端點建立/重新部署/刪除,並就地刷新
  表格——無整頁重載。
- **版本統一**:`app/version.py`、`pyproject.toml` 對齊至 `0.0.2`。
- 測試:Go 抖動解析器 + 環形緩衝測試;Python API/CRUD/權限/隔離測試。

### 0.0.1

- 初始版本:自助對等、公開 looking glass、Telegram bot、admin 儀表板、WSS 節點自動部署、
  雙語 i18n、淺色/深色主題。

---

## 安全

- **ASN 驗證**——建立 peer 需驗證 ASN 擁有權(Kioubit / FindNOC)
- **Admin 存取**——僅操作者的 ASN(`LOCAL_ASN`)授予 admin 權限
- **簽章 session**——以 `SESSION_SECRET` 簽章的 cookie session
- **權限隔離**——API 401(未驗證)對 403(禁止);所有權檢查隱藏跨使用者資源(404)
- **敏感資料隔離**——回應白名單;私鑰絕不離開節點
- **速率限制**——公開 looking-glass 查詢按 IP 速率限制
- **節點驗證**——WSS 連線帶每節點 Bearer token(可輪換)
- **密鑰守衛**——除非明確允許本地測試,backend 拒絕以佔位密鑰啟動
- **輸入驗證**——所有使用者輸入於設定產生前驗證

## 授權

MIT。
