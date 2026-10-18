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

## Deployment

Existing frontend: https://locovoice-skkrrt-train-agent.vercel.app

Existing backend: https://voice-agent-train-scheduling.onrender.com

Keep these services; changing providers does not require a hosting migration. The Docker image uses `APP_ENV=production`, binds Render's `PORT`, disables reload, and excludes local credentials and databases.

Configure these **server-side Render environment variables** before deploying:

| Variable | Value |
| --- | --- |
| `APP_ENV` | `production` |
| `GROQ_API_KEY` | Owner's Groq API key |
| `SARVAM_API_KEY` | Owner's Sarvam API key |
| `ADMIN_TOKEN` | A long randomly generated owner access token; keep it private |
| `ALLOWED_ORIGINS` | `https://locovoice-skkrrt-train-agent.vercel.app` |
| `LLM_MODEL` | `qwen/qwen3.8-27b` (configurable; verify account availability) |
| `SARVAM_STT_MODEL` | `saaras:v3-realtime` |
| `SARVAM_TTS_MODEL` | `bulbul:v3` |
| `SARVAM_VOICE` | `shubh` |

Set Vercel's `VITE_BACKEND_URL` to the existing HTTPS backend URL. Never put provider keys or `ADMIN_TOKEN` in Vercel frontend variables, JavaScript, or Git. The owner dashboard accepts only its access token, held in memory until reload/lock.

Release backend and frontend together: the updated audio protocol requires both. Test a preview deployment with the configured providers before promoting. The `/` response exposes `revision` from `RENDER_GIT_COMMIT` to identify the backend release. `/calls/capabilities` reports missing configuration; `ready` means keys are present, not that provider credit/account access has been validated. A real microphone call must still verify STT, LLM, and TTS against those accounts.

### Budget and hosting limitations

Stay on existing free hosting while validating the integration. No paid plan or credits are provisioned by this repository.
Render Free can spin down when idle and loses its local SQLite database on restarts/redeploys. **Call history is not durable with the default deployment.** For retained history, use a persistent disk on a suitable Render plan or configure a supported external database before treating history as production data. Changing the database requires migrating existing records.

Public calls are limited to two concurrent connections per backend process, three starts per client IP in five minutes, and ten minutes per call. These in-memory limits reset on restart and assume a single worker; they are not a global spending cap. Set provider-side quotas/budgets as well. Streaming currently pauses microphone forwarding while a response is generated or spoken; full-duplex interruption is not implemented.

Sarvam currently lists STT at ₹30/hour and Bulbul v3 at ₹30/10,000 characters. Check current rates and credits in your account: https://docs.sarvam.ai/api/getting-started/pricing
Groq account/model limits: https://console.groq.com/docs/rate-limits
Render free-service behavior: https://render.com/docs/free

## Frontend protocol for the upcoming redesign

1. Read `GET /calls/capabilities`; show the returned message if `ready` is false.
2. Open `/calls/ws/{unique-call-id}` using WSS and send `{"type":"start","sample_rate":16000,"encoding":"linear16"}`.
3. After `ready`, forward mono PCM16 at 16 kHz in `{"type":"audio","audio":"<base64>"}` frames. The supplied AudioWorklet produces 100 ms frames.
4. Display `user_transcript`; pause forwarding on `processing`. On `agent_response`, show text/slots/train results and play each `audio_segments` item with `audio_mime`. Resume microphone forwarding after playback. `audio_error` means text remains available.
5. Select a displayed option with `{"type":"select_train","train_no":"12012","class_code":"CC"}`. A search-result selection starts a seat check, not a simulated booking.
6. Show `error.message`; close on `error.fatal`. On hang-up, send `{"type":"stop"}`, close the socket/audio context, and stop every microphone track.

Admin requests use `Authorization: Bearer <ADMIN_TOKEN>`. `POST /dashboard/config` has been removed. Provider configuration is never supplied by a caller.

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
