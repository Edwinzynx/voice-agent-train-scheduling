# LocoVoice: Indian Railways Voice Agent

LocoVoice uses a React frontend on Vercel and a FastAPI WebSocket backend on Render.
The production speech integration uses Sarvam (realtime STT and Bulbul v3 TTS), with Groq for intent and slot extraction.

## Current functionality

- Live train search and seat checks use the existing ConfirmTkt search endpoint. Upstream failure is reported as an error; missing data is never filled with invented availability or fares.
- Train selection is validated against the selected route, date, and available classes. Confirmation never substitutes a default train.
- Dates use the current date in India. Past/invalid dates are rejected; negated or ambiguous confirmation cannot execute actions.
- Real booking, cancellation, PNR lookup, and running status are **not connected**. Production reports them as unavailable. No payment or refund is performed.
- API keys are managed by the owner in the server environment. There is no user-supplied-key form or configuration-write API.
- Admin analytics, transcripts, provider metadata, and evaluations require an owner bearer token. Public calls do not expose it or provider secrets.
- Local debugging may use browser speech and a rule-based parser. Production never falls back to those modes.
- The project page has a labeled simulated conversation with sample journey data. The sandbox connects to the real backend and puts voice calls first. Metrics, call records, and evaluations are owner-only.
- Text chat uses the same journey and confirmation flow without requesting microphone access or calling Sarvam. Voice calls support typed replies as well.

## Deployment

Existing frontend: https://locovoice-skkrrt-train-agent.vercel.app

Existing backend: https://voice-agent-train-scheduling.onrender.com

Keep these services; changing providers does not require a hosting migration. The Docker image uses `APP_ENV=production`, binds Render's `PORT`, disables reload, and excludes local credentials and databases.

Configure these **server-side Render environment variables** before deploying:

| Variable | Value |
| --- | --- |
| `APP_ENV` | `production` |
| `DATABASE_URL` | Managed PostgreSQL connection URL; use the Neon connection URL with its TLS options, or Render's internal URL for Render Postgres |
| `GROQ_API_KEY` | Owner's Groq API key |
| `SARVAM_API_KEY` | Owner's Sarvam API key |
| `ADMIN_TOKEN` | A long randomly generated owner access token; keep it private |
| `ALLOWED_ORIGINS` | `https://locovoice-skkrrt-train-agent.vercel.app` |
| `LLM_MODEL` | `qwen/qwen3.8-27b` (configurable; verify account availability) |
| `SARVAM_STT_MODEL` | `saaras:v3-realtime` |
| `SARVAM_TTS_MODEL` | `bulbul:v4-flash` |
| `SARVAM_VOICE` | `aarti_hi_customer` (Aarti) |

Set Vercel's `VITE_BACKEND_URL` to the existing HTTPS backend URL. Never put provider keys or `ADMIN_TOKEN` in Vercel frontend variables, JavaScript, or Git. The owner dashboard accepts only its access token, held in memory until reload/lock.

Create `ADMIN_TOKEN` yourself; it is not issued by a provider. Run `python -c "import secrets; print(secrets.token_urlsafe(32))"` locally, save the result as `ADMIN_TOKEN` in Render, and redeploy. Enter that same value in the command center's Owner access field. Public train queries do not require this token.

Release backend and frontend together: the updated audio protocol requires both. Test a preview deployment with the configured providers before promoting. The `/` response exposes `revision` from `RENDER_GIT_COMMIT` to identify the backend release. `/calls/capabilities` reports missing configuration; `ready` means keys are present, not that provider credit/account access has been validated. A real microphone call must still verify STT, LLM, and TTS against those accounts.

### Budget and hosting limitations

Stay on existing free hosting while validating the integration. No paid plan or credits are provisioned by this repository.
Render Free can spin down when idle and loses local files on restarts/redeploys. Production now requires an explicitly configured database URL; use managed PostgreSQL for retained call history. Render's free Postgres expires after 30 days, so it is not a permanent storage solution. No paid resources are created by installing this code.

### Durable call history

1. Use a managed PostgreSQL database independent of the backend filesystem. For the no-cost setup, create a **Neon Free** project in AWS Oregon near `voice-agent-train-scheduling`. Stay on Free and monitor its storage/compute limits. Render's expiring free Postgres is not used for this setup.
2. Set `DATABASE_URL` on the **existing Render backend service** to the Neon connection URL, preserving `sslmode=require` and any other supplied TLS options. Do not add it to Vercel, frontend code, or Git. `postgres://`, `postgresql://`, and `postgresql+psycopg://` are supported. If using paid Render Postgres instead, use its Internal Database URL in the same region.
3. Deploy the updated backend requirements and code. The server initializes missing tables, checks pooled connections before reuse, and refuses to start if database initialization fails. Configure Render's process health-check path as `/`; it deliberately does not query Postgres so continuous probes allow Neon to scale to zero. The owner-only `/dashboard/storage-health` checks storage on demand and returns HTTP 503 if it is unavailable.
4. Complete a test call, confirm it appears in Call Records, restart the backend, and confirm the same record and transcript remain. Call records, turn logs, and evaluation runs persist; live sockets and in-progress dialogue state do not resume after a restart.

For an existing SQLite database, take an offline backup before switching storage. Stop new calls and let active calls finish before exporting; a redeploy may destroy an ephemeral SQLite file. If Render has already removed the file, these changes cannot recover it. Use the correct source file: SQLite paths are relative to the backend's working directory, and the repository may contain more than one local database.

The importer reads the source in read-only mode, preserves IDs and timestamps, copies all three tables in one transaction, verifies row counts, and refuses a populated destination. It does not merge or overwrite records. Set `DATABASE_URL` securely in the migration process environment, using Render's external URL when running outside its private network. Do not paste a URL containing a password into command history.

```sh
# Inspect the offline backup; no destination writes.
python backend/scripts/migrate_sqlite.py --source /path/to/backup.db
# Import into an empty PostgreSQL database while application writes are stopped.
python backend/scripts/migrate_sqlite.py --source /path/to/backup.db --apply
```

Postgres storage is independent of backend deployments. Keep provider backups enabled and test restores. Schema creation handles initial setup only; future schema changes need an explicit migration. Automated CI uses disposable Postgres to verify import and persistence across new database connections.

Public calls are limited to two concurrent connections per backend process, three starts per client IP in five minutes, and ten minutes per call. These in-memory limits reset on restart and assume a single worker; they are not a global spending cap. Set provider-side quotas/budgets as well. Streaming currently pauses microphone forwarding while a response is generated or spoken; full-duplex interruption is not implemented.

Sarvam currently lists STT at ₹30/hour and Bulbul v3 at ₹30/10,000 characters. Check current rates and credits in your account: https://docs.sarvam.ai/api/getting-started/pricing
Groq account/model limits: https://console.groq.com/docs/rate-limits
Render free-service behavior: https://render.com/docs/free

## Frontend protocol for the upcoming redesign

1. Read `GET /calls/capabilities`; `ready` describes voice readiness and `text_ready` describes chat readiness. Show the corresponding `message` or `text_message` when unavailable.
2. Open `/calls/ws/{unique-call-id}` using WSS. For voice, send `{"type":"start","mode":"voice","sample_rate":16000,"encoding":"linear16"}`. For text-only chat, send `{"type":"start","mode":"text"}`; this never opens an STT connection or synthesizes audio. Omitting `mode` retains voice behavior.
3. After `ready`, forward mono PCM16 at 16 kHz in `{"type":"audio","audio":"<base64>"}` frames. The supplied AudioWorklet produces 100 ms frames.
4. Display `user_transcript`; pause forwarding on `processing`. On `agent_response`, show text/slots/train results and play each `audio_segments` item with `audio_mime`. Resume microphone forwarding after playback. `audio_error` means text remains available.
5. Select a displayed option with `{"type":"select_train","train_no":"12012","class_code":"CC"}`. A search-result selection starts a seat check, not a simulated booking.
6. Show `error.message`; close on `error.fatal`. On hang-up, send `{"type":"stop"}`, close the socket/audio context, and stop every microphone track.

Admin requests use `Authorization: Bearer <ADMIN_TOKEN>`. `POST /dashboard/config` has been removed. Provider configuration is never supplied by a caller.

After the greeting, typed replies use `{"type":"user_transcript","text":"..."}` in either session mode. Wait for the current response before sending another turn. Text sessions retain the public connection, start-rate, and duration limits.

## Local debugging and automated checks

```sh
python -m venv .venv
# Activate the virtual environment for your shell.
pip install -r backend/requirements.txt
python -m pytest backend/tests -q
cd frontend
npm ci
npm test
npm run build
```

Tests use isolated databases and provider doubles and never consume production credits. They do not establish that a live provider account is configured. GitHub Actions runs the same regression checks.

For local debugging only, run `python backend/run.py` with `APP_ENV=development` and `npm run dev` inside `frontend`. Without provider keys, local browser speech/parser debugging is enabled. Simulated railway operations require explicit `ALLOW_SIMULATED_RAILWAY=true` and are always disabled in production.

The older four-scenario evaluation suite is a parser/dialogue diagnostic, not proof of live booking or end-to-end voice success. Historical 100% scores are not production capability claims.
