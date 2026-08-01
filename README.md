# AutoPeer

**A self-service autopeering platform and public Looking Glass for dn42 networks.**

AutoPeer automates establishing BGP peers across distributed dn42 nodes: users verify ASN
ownership, pick a node, supply a WireGuard public key, and receive a ready-to-use WireGuard +
BIRD config in minutes — no manual router configuration. Manage everything via the web UI, the
Telegram bot, or the REST API (`/api/v1`).

> Version: **0.0.2** · Python 3.11+ · Go 1.21+ · MIT License

---

## Table of Contents

- [Running](#running)
- [Structure](#structure)
- [API](#api)
- [Updates (Changelog)](#updates-changelog)
- [Security](#security)

---

## Running

### Prerequisites

- Python 3.11+, Go 1.21+
- A public HTTPS domain (production) or `--allow-http` for local testing
- WireGuard + BIRD on each node router

### Backend setup

```bash
git clone https://github.com/anncix/autopeer.git
cd autopeer

cp .env.example .env          # then edit .env (see below)
python3 -m pip install -r requirements.txt
python3 start.py
```

`.env` (required secrets — the backend refuses to start with placeholder values unless
`ALLOW_INSECURE_DEFAULTS=1`):

```bash
DOMAIN=your.domain.com
LOCAL_ASN=4242420000
SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
TELEGRAM_BACKEND_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Optional
TELEGRAM_BOT_TOKEN=            # from BotFather; leave blank to disable the bot
FINDNOC_API_TOKEN=             # optional FindNOC quick-login for the bot
ALLOW_INSECURE_DEFAULTS=0      # set 1 only for local testing
```

Place Kioubit's signing public key at `app/keys/public_key.pem` (ASN-ownership verification).

### Node service setup (on each router)

```bash
cd cmd/node
go build -o node .
cd ../..

cp config.example.json config.json   # edit name/token/wireguard keys
./node -config ./config.json
```

`config.json`:

| Key | Description |
|-----|-------------|
| `name` | Node name matching the backend record |
| `token` | Bearer token for the WSS connection (from the admin node detail / reset-token) |
| `backend_wss_url` | Backend WebSocket URL (`wss://host/api/nodes/ws`) |
| `wireguard_public_key` / `wireguard_private_key` | Router WG keys (private never leaves the node) |
| `bird_peer_dir` / `wireguard_peer_dir` | Dirs for generated BIRD snippets / WG configs |
| `deploy_reload_cmd` | Post-deploy reload (e.g. `birdc c`) |
| `birdc_path` / `wg_path` / `wg_quick_path` / `ping_path` / `traceroute_path` / `mtr_path` | Binary paths |

### Launch options

| Flag | Description |
|------|-------------|
| `--allow-http` | Local testing; permits non-HTTPS `DOMAIN` |
| `--backend-only` | Start only the FastAPI backend |
| `--bot-only` | Start only the Telegram bot |
| `--host` / `--port` | Override the backend bind address |

### Backend environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `AutoPeer` | Display name in the UI |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | Bind address |
| `DOMAIN` | `127.0.0.1:8000` | Public HTTPS domain |
| `SESSION_SECRET` | *(insecure default)* | Signed-cookie session secret |
| `DATABASE_URL` | `sqlite:///./autopeer.db` | Database URL |
| `LOCAL_ASN` | *(empty)* | Operator ASN — grants admin privileges |
| `KIOUBIT_PUBLIC_KEY_PATH` | `app/keys/public_key.pem` | Kioubit ECDSA public key |
| `TELEGRAM_BOT_TOKEN` | *(empty)* | Telegram BotFather token |
| `TELEGRAM_BACKEND_SECRET` | *(insecure default)* | Bot ↔ backend shared secret |
| `FINDNOC_API_TOKEN` / `FINDNOC_API_URL` | *(empty)* / `https://findnoc.ox5.cc` | Optional FindNOC login |
| `LG_RATE_LIMIT` / `LG_RATE_WINDOW_SECONDS` | `20` / `60` | Public LG rate limit per IP |
| `FORWARDED_IP_HEADER` | *(empty)* | Trusted client-IP header (reverse proxy only) |

---

## Structure

```
┌─────────────────────────────────────────────────┐
│  Browser / curl          Telegram bot           │
│  (Web UI + /api/v1)      (/api/telegram/*)      │
└──────────────────────┬──────────────────────────┘
                       │
            ┌──────────▼──────────┐
            │  Control plane      │  FastAPI + SQLAlchemy + SQLite
            │  (Python, app/)     │  · ASN verification (Kioubit/FindNOC)
            │                     │  · Peer lifecycle + config generation
            │                     │  · REST API (/api/v1) + Web UI
            └──────────┬──────────┘
                       │ WSS (token auth)
            ┌──────────▼──────────┐
            │  Node service (Go)  │  one per router
            │  cmd/node, internal/│  · WireGuard + BIRD deploy
            │                     │  · Looking-glass command exec
            └─────────────────────┘
```

```
autopeer/
├── app/
│   ├── api/              JSON APIs
│   │   ├── deps.py       require_api_user / require_api_admin (401/403 JSON)
│   │   ├── schemas.py    Pydantic response models (sensitive-data whitelists)
│   │   ├── telegram.py   Bot-only API (X-Backend-Secret)
│   │   └── v1/           REST CRUD API (peers, nodes, admin)
│   ├── auth/             Kioubit, FindNOC, sessions
│   ├── bot/              Telegram bot
│   ├── db/               SQLAlchemy models + session
│   ├── intra/            Intra-link (iBGP/OSPF backbone) config + deploy
│   ├── lg/               Looking-glass client + rate limiter
│   ├── peer/             Peer validation, config generation, deployment
│   ├── templates/        Jinja2 HTML (admin/, macros.html, …)
│   ├── static/           CSS, JS, i18n.js
│   ├── web/              HTML routes (pages, portal, admin, lg)
│   ├── node_ws.py        Node WebSocket hub
│   ├── version.py        Version (0.0.2)
│   └── main.py           FastAPI app + router wiring
├── cmd/node/             Node service entrypoint (Go)
├── internal/             Node service internals (Go)
│   ├── api/              Command dispatcher (+ BGP flap detection)
│   ├── config/           JSON config loader
│   └── runner/           Deployment runner
├── config.example.json   Node service config template
├── start.py              Launcher (backend + bot)
├── pyproject.toml        Python project + ruff config
└── requirements.txt
```

---

## API

AutoPeer exposes three JSON API surfaces. The web UI and `/api/v1` share session-cookie auth;
`/api/telegram/*` is machine-to-machine (shared secret); the node WSS channel is token-auth.

### `POST /lg` — Looking Glass (anonymous)

Query type in `{ping, traceroute, mtr, bird, route}`. With header `X-Requested-With: fetch`
returns `{ok, output, query_type}`; otherwise renders the HTML page.

### `/api/v1/*` — REST CRUD API (session auth)

All `/api/v1` endpoints except the public node list require an authenticated session cookie
(browser login). Auth failures return **401** (not logged in) or **403** (logged in, no
permission) as JSON — distinct codes so clients can tell them apart. Validation errors return
**400**; conflicts (duplicate name, node-with-peers) return **409**.

**Peers** (`/api/v1/peers`) — user-scoped; you manage only your own peers. A foreign peer id
returns **404** (ownership hides existence). ASN is taken from your session, so you cannot peer
as another AS.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/peers` | user | List your peers |
| POST | `/api/v1/peers` | user | Create a peer (201) |
| GET | `/api/v1/peers/{id}` | user | Get your peer |
| PATCH | `/api/v1/peers/{id}` | user | Partial update; `status=disabled` tears down, `redeploy=true` re-pushes |
| DELETE | `/api/v1/peers/{id}` | user | Delete + best-effort teardown |

**Nodes** (`/api/v1/nodes` public, `/api/v1/admin/nodes` admin)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/nodes` | anon | List enabled nodes (public fields only) |
| GET | `/api/v1/nodes/{id}` | anon | Node detail (public fields) |
| GET | `/api/v1/admin/nodes` | admin | List all nodes incl. token + runtime |
| POST | `/api/v1/admin/nodes` | admin | Create node (201); token generated server-side, returned once |
| GET | `/api/v1/admin/nodes/{id}` | admin | Node detail incl. token |
| PATCH | `/api/v1/admin/nodes/{id}` | admin | Partial update |
| DELETE | `/api/v1/admin/nodes/{id}` | admin | Delete (409 if peers still homed) |
| POST | `/api/v1/admin/nodes/{id}/reset-token` | admin | Rotate the node agent token |

**Admin** (`/api/v1/admin/*`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/peers` | List all peers (with deploy_output) |
| GET | `/api/v1/admin/peers/{id}` | Any peer detail (with deploy_output) |
| GET | `/api/v1/admin/nodes/{id}/intra-links` | List backbone links on a node |
| POST | `/api/v1/admin/nodes/{id}/intra-links` | Create intra-link (optionally bidirectional) |
| DELETE | `/api/v1/admin/nodes/{id}/intra-links/{link_id}` | Delete intra-link |
| GET | `/api/v1/admin/users` | List users (Telegram chat ids / mnt JSON stripped) |

### `/api/telegram/*` — Bot API (shared secret)

Requires header `X-Backend-Secret` == `TELEGRAM_BACKEND_SECRET`. Peer CRUD, LG queries, login
challenge/verify, FindNOC login, batch status — see `app/api/telegram.py`.

### Sensitive-data isolation

API responses are built from explicit Pydantic whitelists (`app/api/schemas.py`), never raw ORM
rows:

- `Node.token` (agent credential) and `system_status_json` appear **only** in the admin
  `NodeAdmin` view — never in the anonymous `NodePublic` list.
- `deploy_output` (may contain node-side hostnames/paths) is absent from the owner `PeerOut`
  view, present only in the admin `PeerAdmin` view.
- `UserOut` strips Telegram chat ids and ASN-identity maintainer JSON (PII).
- WireGuard **private keys never enter the control-plane DB** — configs use the
  `{{WIREGUARD_PRIVATE_KEY}}` placeholder, substituted by the node agent at deploy time.

---

## Updates (Changelog)

### 0.0.2

- **REST CRUD API** (`/api/v1`): full create/read/update/delete for peers (user-scoped, ownership-
  enforced), nodes (public read + admin CRUD), intra-links, and admin peer/user lists. Reuses the
  same service functions as the HTML routes, so validation and deploy logic stay in one place.
- **Permission isolation**: new `require_api_user` / `require_api_admin` dependencies return
  JSON 401/403 (distinct from the HTML redirect-to-login flow). Cross-user peer access returns
  404 to hide existence.
- **Sensitive-data isolation**: Pydantic response whitelists strip `Node.token`,
  `deploy_output` (non-admin), and Telegram PII from every API response.
- **BGP flap detection** (P2): the Go node agent polls `birdc show protocols`, diffs BGP state
  transitions (up/start/down) into a bounded ring buffer, and exposes `flap.check` / `flap.events`
  commands rendered on a new admin flap page.
- **Bidirectional intra-link creation** (P2): a single create optionally provisions the matching
  reverse link on the remote node, via a shared `_provision_intra_link` helper.
- **Progressive-enhancement link management** (P3): the links tab creates / redeploys / deletes
  via `fetch` against JSON endpoints and refreshes the table in place — no full page reload.
- **Version unification**: `app/version.py`, `pyproject.toml` aligned to `0.0.2`.
- Tests: Go flap parser + ring-buffer tests; Python API/CRUD/permission/isolation tests.

### 0.0.1

- Initial release: self-service autopeering, public looking glass, Telegram bot, admin dashboard,
  node auto-deployment over WSS, bilingual i18n, light/dark themes.

---

## Security

- **ASN verification** — peer creation requires verified ASN ownership (Kioubit / FindNOC)
- **Admin access** — only the operator's ASN (`LOCAL_ASN`) grants admin privileges
- **Signed sessions** — cookie sessions signed with `SESSION_SECRET`
- **Permission isolation** — API 401 (unauth) vs 403 (forbidden); ownership checks hide
  cross-user resources (404)
- **Sensitive-data isolation** — response whitelists; private keys never leave the node
- **Rate limiting** — public looking-glass queries are rate-limited per IP
- **Node authentication** — WSS connections bear a per-node bearer token (rotatable)
- **Secret guard** — the backend refuses to start with placeholder secrets unless explicitly
  allowed for local testing
- **Input validation** — all user input is validated before config generation

## License

MIT.
