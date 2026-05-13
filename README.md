# Gate MoonHunter AI

Production-style realtime scanner for **Gate.io** spot markets: volume spikes, volatility, breakout-style momentum, liquidity proxies, whale-sized trade hints, optional social velocity, rug-risk heuristics, and a composite **Moonshot score** with confidence and risk bands. Data is pulled live via **CCXT** (no fabricated prices).

## Quick start

1. Optional: copy and customize environment values (otherwise Compose uses `.env.example` as bundled defaults):

   ```bash
   copy .env.example .env
   ```

   To use a separate env file with Compose: `docker compose --env-file .env up --build` and adjust `env_file` in `docker-compose.yml` if needed.

2. Build and run (Compose loads defaults from `.env.example`; edit that file or add a custom env file for Telegram / Twitter / Gate keys):

   ```bash
   docker compose up --build
   ```

3. Open the dashboard: [http://localhost:3000](http://localhost:3000)  
4. API docs: [http://localhost:8000/docs](http://localhost:8000/docs)  
5. WebSocket: `ws://localhost:8000/ws/market`

### Core API endpoints

- `GET /api/latest`
- `GET /api/moonshots`
- `GET /api/top-gainers`
- `GET /api/top-volume`
- `GET /api/heatmap`
- `GET /api/smart-money`
- `GET /api/risk-analysis`
- `GET /api/alerts`

### Optional: Gate.io API keys

Public market data works without keys. Adding `GATE_API_KEY` / `GATE_API_SECRET` increases rate limits and stability for heavy scanning.

### Optional: Telegram

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env.example` (or your env file) if you use one. Alerts fire when moonshot score and risk pass the configured thresholds.

### Optional: Social velocity

Set `TWITTER_BEARER_TOKEN` for lightweight recent-mention counts on top symbols (best-effort; rate limits apply).

## Architecture

| Service   | Role |
|-----------|------|
| `api`     | FastAPI REST + WebSocket fan-out; background asyncio scanner |
| `postgres`| Symbols, ticker snapshots, signals, alert log |
| `redis`   | Latest-scan cache for REST + WebSocket replay on connect |
| `web`     | Next.js 15 dashboard (TradingView-inspired dark UI) |

## Scoring model

Features are normalized and combined into **Moonshot** (0–100), **Confidence** (0–100), and **Risk** (0–100, higher = riskier). The backend loads `models/moonshot_xgb.json` if present (train with your own historical labels); otherwise a calibrated weighted ensemble runs using `sklearn` preprocessing helpers and `numpy`.

Scanner and routes are intentionally documented with short comments and explicit field naming so payload contracts stay stable for realtime UI consumers.

## Development (without Docker)

**Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
set DATABASE_URL=postgresql://moonhunter:moonhunter@localhost:5432/moonhunter
set REDIS_URL=redis://localhost:6379/0
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

## License

MIT — use at your own risk. Not financial advice. Crypto trading involves substantial risk.
