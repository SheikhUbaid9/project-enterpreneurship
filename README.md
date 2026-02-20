# Multi-Platform Inbox MCP Server (v1.0)

Microservices SaaS stack with a unified MCP gateway for inbox operations across platforms.

## Architecture

- `auth-service` (FastAPI, JWT, RBAC, seeded users)
- `email-adapter-service` (FastAPI, async SQLAlchemy, mock email inbox data)
- `mcp-gateway-service` (REST + JSON-RPC 2.0 + SSE + FastMCP tool registration)
- `slack-adapter-service` (stub)
- `whatsapp-adapter-service` (stub)
- `shared` (shared Pydantic models + AES-256 token encryption helper)
- `frontend-dashboard` (Next.js 14 App Router + TypeScript + Tailwind + shadcn-style components)

Patterns implemented:

- Microservices
- Database-per-service (auth DB + email DB)
- Adapter pattern
- Repository pattern
- Gateway pattern
- Redis Streams for MVP event logging

## Ports

- Frontend dashboard: `3000`
- MCP Gateway: `8000`
- Auth Service: `8001`
- Email Adapter: `8002`
- Slack Adapter (stub): `8003`
- WhatsApp Adapter (stub): `8004`
- Postgres Email: `5432`
- Postgres Auth: `5433`
- Redis: `6379`
- Zookeeper (optional): `2181`
- Kafka (optional): `9092`

## Prerequisites

- Docker Desktop / Docker Engine
- Docker Compose
- Node.js 20+ (only if you want to run frontend locally outside Docker)
- Python 3.12+ (only if you want to run services locally outside Docker)

## 1) Environment Setup

Copy root env:

```bash
cp .env.example .env
```

Generate a secure token encryption key (32-byte base64):

```bash
python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

Paste into `.env` as `TOKEN_ENCRYPTION_KEY`.

## 2) Start the Full Stack

```bash
docker compose up --build
```

Optional Kafka/Zookeeper profile:

```bash
docker compose --profile kafka up --build
```

## 3) Health Checks

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8000/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

## 4) Seeded Login Users (Auth Service)

- Owner: `owner@inbox.local` / `OwnerPass!123`
- Admin: `admin@inbox.local` / `AdminPass!123`
- Member: `member@inbox.local` / `MemberPass!123`

Get token:

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@inbox.local","password":"OwnerPass!123"}'
```

Use returned `access_token` as `Bearer <TOKEN>`.

## 5) REST API Examples (Gateway)

Get unread across all platforms:

```bash
curl "http://localhost:8000/messages/unread?platform=all&limit=50" \
  -H "Authorization: Bearer <TOKEN>"
```

Reply to a message:

```bash
curl -X POST http://localhost:8000/messages/<MESSAGE_ID>/reply \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"platform":"email","content":"Thanks, received."}'
```

Mark messages read:

```bash
curl -X PATCH http://localhost:8000/messages/read \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"platform":"email","message_ids":["<MESSAGE_ID>"]}'
```

Platform status:

```bash
curl http://localhost:8000/platforms \
  -H "Authorization: Bearer <TOKEN>"
```

Get thread:

```bash
curl "http://localhost:8000/threads/<THREAD_ID>?platform=email" \
  -H "Authorization: Bearer <TOKEN>"
```

Prioritize messages:

```bash
curl -X POST http://localhost:8000/messages/prioritize \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"criteria":"urgency","messages":[{"id":"1","priority":"urgent"},{"id":"2","priority":"low"}]}'
```

Summarize placeholder:

```bash
curl "http://localhost:8000/threads/<THREAD_ID>/summary?platform=email" \
  -H "Authorization: Bearer <TOKEN>"
```

Search placeholder:

```bash
curl "http://localhost:8000/messages/search?q=invoice&platform=all" \
  -H "Authorization: Bearer <TOKEN>"
```

## 6) MCP JSON-RPC Examples

Initialize:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

List tools:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Call `get_unread_messages`:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":3,
    "method":"tools/call",
    "params":{
      "name":"get_unread_messages",
      "arguments":{"platform":"all","limit":25}
    }
  }'
```

Call `send_reply`:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":4,
    "method":"tools/call",
    "params":{
      "name":"send_reply",
      "arguments":{"platform":"email","message_id":"<MESSAGE_ID>","content":"Acknowledged."}
    }
  }'
```

SSE stream:

```bash
curl -N http://localhost:8000/mcp/sse \
  -H "Authorization: Bearer <TOKEN>"
```

## 7) Frontend Dashboard

Open:

- `http://localhost:3000/login`

Pages:

- `/login`
- `/inbox`
- `/thread/[id]`
- `/platforms`
- `/settings`

Features included:

- Sidebar navigation
- Top search bar
- Platform badges
- Priority badges
- Thread summary placeholder
- Reply workflow
- Protected routes via middleware + token cookie

## 8) Local Dev Without Docker (optional)

Backend services:

- Install dependencies per service from each `requirements.txt`
- Install `shared` as editable: `pip install -e ./shared`
- Run with `uvicorn app.main:app --reload --port <service-port>`

Frontend:

```bash
cd frontend-dashboard
npm install
npm run dev
```

## Notes

- Old TypeScript services (`api/`, `worker/`, `mcp/`) are still present in the repo from previous iteration.
- v1.0 run path is the new Python microservices + `frontend-dashboard`.
