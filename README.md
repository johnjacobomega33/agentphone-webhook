# agentphone-webhook

Minimal HTTPS webhook receiver for AgentPhone testing (Render free tier).

- `GET /` — health (`ok`)
- `POST /webhook` — store event (last 100 in memory) + stdout log; returns `{"ok":true}`
- `GET /events?key=...` — dump stored events (requires `EVENTS_KEY`)

Env: `EVENTS_KEY`, `AGENTPHONE_WEBHOOK_SECRET` (placeholder), `PORT` (Render).
