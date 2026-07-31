# AutoPeer

**A self-service autopeering platform and public Looking Glass for dn42 networks.**

AutoPeer automates the process of establishing BGP peers across distributed dn42 nodes. Users verify ASN ownership, select a node, provide their WireGuard public key, and receive a ready-to-use WireGuard + BIRD configuration in minutes — no manual router configuration required.

## Key Features

- **Self-service autopeering** — Create and manage dn42 peer sessions through a clean web UI or Telegram bot
- **Global bilingual support** — English / 中文 with instant toggle in the top navigation bar
- **Light & dark themes** — Switch between light and dark modes, choice is persisted
- **Public Looking Glass** — Run ping, traceroute, mtr, and BIRD route queries across all nodes
- **Telegram bot integration** — Full peer lifecycle management from Telegram
- **Admin dashboard** — Node health, peer status, deployment tracking, user management
- **Node auto-deployment** — WireGuard + BIRD configs are automatically generated and deployed via WSS

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  AutoPeer Platform               │
├─────────────────────────────────────────────────┤
│  Web UI (FastAPI + Jinja2)                       │
│  ├── i18n (English / 中文)                       │
│  ├── Light / Dark Theme                          │
│  └── Responsive Layout                           │
├─────────────────────────────────────────────────┤
│  Backend (FastAPI + SQLite)                      │
│  ├── ASN ownership verification (Kioubit)        │
│  ├── Peer lifecycle management                  │
│  ├── WireGuard + BIRD config generation         │
│  └── Bot-only REST API                          │
├─────────────────────────────────────────────────┤
│  Node Service (Go)                               │
│  ├── WSS connection to backend                   │
│  ├── WireGuard config deployment                 │
│  ├── BIRD peer snippet management                │
│  └── Looking Glass command execution             │
├─────────────────────────────────────────────────┤
│  Telegram Bot                                    │
│  ├── Login / Logout                              │
│  ├── Create / Edit / Delete peers                │
│  └── Looking Glass queries                      │
└─────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, SQLite |
| Frontend | Jinja2, Vanilla JS, CSS Variables |
| Node Service | Go 1.21+, WireGuard, BIRD |
| Auth | Kioubit.dn42, Telegram |
| Bot | python-telegram-bot |
| i18n | Custom lightweight client-side translations |

## Quick Start

### Prerequisites

- Python 3.11+
- Go 1.21+
- A public domain (for production)
- WireGuard + BIRD on each node router

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/anncix/autopeer.git
cd autopeer

# Configure environment
cp .env.example .env

# Install dependencies
python3 -m pip install -r requirements.txt

# Start the platform
python3 start.py
```

Edit `.env` before deployment:

```bash
# Required
DOMAIN=your.domain.com
LOCAL_ASN=4242420000
SESSION_SECRET=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(32))">
TELEGRAM_BACKEND_SECRET=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Optional
TELEGRAM_BOT_TOKEN=<botfather-token>
ALLOW_INSECURE_DEFAULTS=0
```

Place Kioubit's signing public key at `app/keys/public_key.pem`.

### Node Service Setup

Build and deploy the node service to each router:

```bash
cd cmd/node
go build -o node .
cd ../..

cp internal/config/config.example.json config.json

# Edit config.json with your node settings
./node -config ./config.json
```

### Launch Options

| Flag | Description |
|------|-------------|
| `--allow-http` | Local testing mode, allows non-HTTPS `DOMAIN` |
| `--backend-only` | Start only the FastAPI backend |
| `--bot-only` | Start only the Telegram bot |
| `--host` / `--port` | Override backend bind address |

## Web Interface

| Route | Description |
|-------|-------------|
| `/` | Home page: hero, platform stats, how-to-peer guide |
| `/lg` | Public Looking Glass (ping, traceroute, mtr, route) |
| `/login` | ASN login via Kioubit |
| `/nodes` | Public node directory with live status |
| `/portal` | Your Peers dashboard |
| `/portal/new` | Create a new peer session |
| `/portal/peers/{id}` | Peer detail with WireGuard/BIRD configs |
| `/admin` | Admin overview: stats, recent activity |
| `/admin/nodes` | Node management (add, edit, enable/disable) |
| `/admin/nodes/new` | Add a new node |
| `/admin/peers` | Peer management (edit, redeploy, delete) |
| `/admin/peers/new` | Create a peer on behalf of a user |
| `/admin/users` | User management |
| `/admin/lg-log` | Looking Glass audit log |

## How Peering Works

1. **Login** — Verify ASN ownership via Kioubit.dn42
2. **Create Peer** — Select a node, provide WireGuard public key and endpoint
3. **Configure** — Choose tunnel IP (link-local or ULA), MTU, BGP extensions
4. **Deploy** — Auto-generated WireGuard + BIRD configs are pushed to the node
5. **Go Live** — Copy your side parameters and bring up the tunnel

## Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `AutoPeer` | Display name in UI |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | Bind address |
| `DOMAIN` | - | Public HTTPS domain |
| `SESSION_SECRET` | - | Signed-cookie session secret |
| `DATABASE_URL` | `sqlite:///./autopeer.db` | Database URL |
| `LOCAL_ASN` | - | Operator ASN (admin access) |
| `KIOUBIT_PUBLIC_KEY_PATH` | `app/keys/public_key.pem` | Kioubit ECDSA public key |
| `TELEGRAM_BOT_TOKEN` | - | Telegram BotFather token |
| `TELEGRAM_BACKEND_SECRET` | - | Bot-backend shared secret |
| `LG_RATE_LIMIT` | `20` | Public LG requests per IP per window |
| `FORWARDED_IP_HEADER` | - | Trusted client-IP header |

### Node Service Configuration

| Key | Description |
|-----|-------------|
| `name` | Node name matching backend record |
| `token` | Bearer token for WSS connection |
| `backend_wss_url` | Backend WebSocket URL |
| `wireguard_public_key` | Router public key (reported to peers) |
| `wireguard_private_key` | Router private key (for `wg-quick`) |
| `bird_peer_dir` | Directory for generated BIRD snippets |
| `wireguard_peer_dir` | Directory for WireGuard configs |
| `deploy_reload_cmd` | Post-deploy reload command (e.g., `birdc c`) |

## Project Structure

```
autopeer/
├── app/
│   ├── api/              Bot-only REST API
│   ├── auth/             Kioubit, FindNOC, sessions
│   ├── bot/              Telegram bot
│   ├── db/               SQLAlchemy models
│   ├── lg/               Looking Glass client
│   ├── peer/             Peer validation, config, deployment
│   ├── templates/        Jinja2 HTML templates
│   │   ├── admin/        Admin panel templates
│   │   └── macros.html   Reusable template macros
│   ├── static/           CSS, JavaScript, i18n
│   │   ├── i18n.js       Client-side internationalization
│   │   └── styles.css    Theme variables and styles
│   ├── web/              Web routes (pages, portal, admin)
│   ├── node_ws.py        Node WebSocket hub
│   ├── version.py        Version info
│   └── main.py           FastAPI application
├── cmd/node/             Node service (Go)
├── internal/            Node service internals
│   ├── api/              Command dispatcher
│   ├── config/           JSON config loader
│   └── runner/           Deployment logic
├── docs/                 Additional documentation
├── start.py              Launcher script
├── requirements.txt      Python dependencies
└── README.md             This file
```

## Security

- **ASN verification** — All peer creation requires verified ASN ownership
- **Admin access** — Only the operator's ASN (`LOCAL_ASN`) grants admin privileges
- **Signed sessions** — Cookie-based sessions with signed secrets
- **Rate limiting** — Looking Glass queries are rate-limited
- **Node authentication** — WSS connections bear token-based authentication
- **Input validation** — All user input is validated before config generation

## License

This project is released under the MIT License.

## Support

For issues, please open a GitHub issue or contact the maintainers.
