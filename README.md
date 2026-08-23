# Voice AI Patient Registration System

A voice-based AI patient registration system for healthcare intake. Callers dial a phone number, a Vapi voice agent conversationally collects patient demographics, confirms the data, persists it to SQLite, and exposes it via a REST API.

> **Demo only** — do not store real patient data. This system is not HIPAA-compliant.

## Live Deployment

| Resource | URL |
|----------|-----|
| API Base URL | `https://web-production-fe469.up.railway.app` |
| Phone Number | `+1 (843) 969-4359` |
| Dashboard | `https://web-production-fe469.up.railway.app/dashboard` |
| API Docs | `https://web-production-fe469.up.railway.app/docs` |

## Architecture

```
Caller Phone
     │
     ▼
┌─────────────┐
│  Vapi Voice │  ← STT, LLM, TTS, tool-calling
│  Assistant  │
└──────┬──────┘
       │ HTTP tool calls (lookup, create, update)
       ▼
┌─────────────┐
│   FastAPI   │  ← REST API, validation, logging
│   Backend   │
└──────┬──────┘
       │ SQLAlchemy async
       ▼
┌─────────────┐
│   SQLite    │  ← Patient records (soft delete)
└─────────────┘
```

**Flow:** Caller dials Vapi phone number → assistant greets and collects fields conversationally → on phone number, calls `GET /patients/lookup` for duplicate detection → after explicit confirmation, calls `POST /patients` or `PUT /patients/{id}` → data persisted to SQLite → viewable via REST API or `/dashboard`.

## Tech Stack Justification

| Choice | Why |
|--------|-----|
| **Vapi** over raw Twilio | Vapi bundles STT + LLM + TTS + tool-calling into one platform. Raw Twilio would require wiring Deepgram/Whisper, OpenAI, and ElevenLabs separately — too much integration work for a 3-hour assessment. |
| **FastAPI** | Async-native, automatic OpenAPI docs, Pydantic v2 integration — ideal for a tool-calling API backend. |
| **SQLite** over Postgres | Zero-config, file-based, perfect for a demo/take-home. Railway supports both, but SQLite eliminates database provisioning overhead. Swap to Postgres by changing `DATABASE_URL` only. |
| **SQLAlchemy async + aiosqlite** | Production-grade ORM patterns without blocking the event loop. |

## Quick Start (Local)

### Prerequisites

- Python 3.11+
- A [Vapi](https://vapi.ai) account (for voice integration)
- An OpenAI API key (used by Vapi for the LLM)

### Setup

```bash
# Clone and enter the project
cd "D:\Voice AI"

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env template
copy .env.example .env
# Edit .env with your keys
```

### Run Locally

```bash
# Start the API server (reads PORT from env, defaults to 8000)
python run.py

# Or directly:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is available at:
- http://localhost:8000/docs — Swagger UI
- http://localhost:8000/dashboard — Patient dashboard
- http://localhost:8000/health — Health check

A demo patient (Jane Doe) is seeded automatically on first boot.

### Run Tests

```bash
pytest -v
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./patients.db` | Async SQLite connection string |
| `PORT` | No | `8000` | Server port (Railway sets this automatically) |
| `VAPI_API_KEY` | Yes (for voice) | — | Vapi dashboard API key |
| `VAPI_PHONE_NUMBER_ID` | Yes (for voice) | — | Vapi phone number ID for inbound calls |
| `OPENAI_API_KEY` | Yes (for voice) | — | OpenAI key (configured in Vapi assistant) |

## API Endpoints

All responses use the envelope format:

```json
{ "data": {...}, "error": null }
```

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/patients` | List patients (excludes soft-deleted). Query: `?last_name=`, `?date_of_birth=`, `?phone_number=` |
| `GET` | `/patients/{id}` | Get single patient by UUID |
| `POST` | `/patients` | Create patient (201) |
| `PUT` | `/patients/{id}` | Partial update |
| `DELETE` | `/patients/{id}` | Soft delete (sets `deleted_at`) |
| `GET` | `/patients/lookup?phone_number=` | Duplicate detection for voice agent |

### Example: Create Patient

```bash
curl -X POST http://localhost:8000/patients \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "date_of_birth": "1990-01-15",
    "sex": "Male",
    "phone_number": "5551234567",
    "address_line_1": "123 Main St",
    "city": "Chicago",
    "state": "IL",
    "zip_code": "60601"
  }'
```

## Deploy to Railway

1. Push this repo to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Connect the GitHub repo — Railway auto-detects Python via Nixpacks
4. Set environment variables in Railway dashboard (at minimum `DATABASE_URL` if you want a persistent volume path)
5. Railway sets `PORT` automatically — no code changes needed
6. Note the public URL (e.g., `https://voice-ai-patient-reg.up.railway.app`)

For persistent SQLite on Railway, mount a volume and set:
```
DATABASE_URL=sqlite+aiosqlite:////Data/patients.db
```
This deployment's volume persistence has been verified: records survive across redeploys.

## Vapi Assistant Setup

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai) → Assistants → Create
2. Paste the system prompt from [`vapi_system_prompt.md`](vapi_system_prompt.md)
3. Configure the model (GPT-4o or similar) with your OpenAI API key
4. Add three tools pointing at your deployed API base URL's Vapi adapter endpoints (Vapi always POSTs the tool-call envelope to `server.url` — these adapter routes translate it to the REST layer):
   - `lookup_patient_by_phone` → `POST {API_BASE_URL}/vapi/lookup_patient`
   - `create_patient` → `POST {API_BASE_URL}/vapi/create_patient`
   - `update_patient` → `POST {API_BASE_URL}/vapi/update_patient`
5. See [`vapi_tools.json`](vapi_tools.json) for tool parameter schemas
6. Enable `endCallFunctionEnabled` and set `endCallPhrases` to a phrase unique to the closing line only, e.g. `["You're all set"]` — relying solely on the LLM to invoke an `endCall` tool call in the same turn as its closing message is unreliable in practice. Be careful the phrase doesn't also appear in the opening greeting or mid-call prompts, or the call will hang up early.
7. Assign a phone number to the assistant
8. Test with a live call

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| Future date of birth | API returns 422; agent re-prompts for DOB only |
| Invalid phone (not 10 digits) | API returns 422; agent re-prompts for phone only |
| Call drops mid-registration | No partial record written — save only on explicit confirmation |
| Database write failure | API returns 500 with envelope; agent tells caller and offers retry |
| Caller wants to restart | Agent clears state and restarts greeting without ending call |
| Duplicate phone number | Lookup returns existing record; agent offers update vs. new record |

## Known Limitations

- **No HIPAA compliance** — demo system with SQLite, no encryption at rest, no audit logging beyond stdout
- **No call-drop resume** — if a call disconnects mid-registration, the caller must start over
- **Single language** — English only (preferred_language field exists but agent speaks English)
- **SQLite persistence on Railway** — requires a mounted volume with `DATABASE_URL` pointed at it (done for this deployment; verified data survives redeploys)
- **No authentication** — API is open (appropriate for demo, not production)
- **No appointment scheduling**

## Next Steps

- [ ] Mount Railway volume for persistent SQLite
- [ ] Add API authentication (API key or JWT)
- [ ] Implement call-drop resume via Vapi session/conversation state
- [ ] Store call transcripts via Vapi end-of-call webhook
- [ ] Migrate to PostgreSQL for production
- [ ] Multi-language support via Vapi language settings
- [ ] HIPAA-compliant hosting (AWS HIPAA BAA, encrypted storage)

## Vapi System Prompt

The full conversational system prompt is in [`vapi_system_prompt.md`](vapi_system_prompt.md). Copy it into your Vapi assistant configuration.

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI app, CORS, error handlers
│   ├── config.py            # Settings from env vars
│   ├── database.py          # Async SQLAlchemy engine + sessions
│   ├── seed.py              # Demo patient seed
│   ├── models/patient.py    # SQLAlchemy Patient model
│   ├── schemas/             # Pydantic Create/Update/Response schemas
│   ├── routers/patients.py  # All 6 API endpoints
│   └── services/            # Database operations + structured logging
├── static/dashboard.html    # Minimal patient listing dashboard
├── tests/                   # pytest + httpx async tests
├── vapi_system_prompt.md    # Voice agent system prompt
├── vapi_tools.json          # Tool definitions for Vapi
├── requirements.txt
├── railway.toml             # Railway deployment config
└── Procfile                 # Process definition
```
