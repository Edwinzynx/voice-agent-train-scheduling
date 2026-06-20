# LocoVoice: Indian Railways Voice Agent & Analytics Dashboard

LocoVoice is a state-of-the-art, premium conversational AI voice agent and real-time dashboard designed for booking tickets, checking seat availability, and tracking PNR statuses on Indian Railways (IRCTC). 

The system leverages a hybrid architecture combining a FastAPI WebSocket backend, a React/Vite glassmorphic frontend, a custom Finite State Machine (FSM) coordinator, and a Groq-powered LLM brain with local rule-based fallbacks.

---

## 🚀 Key Features

*   **Multilingual Dialect Support:** Seamlessly converse in **English**, **Hindi**, and **Hinglish** (mixed Hindi-English).
*   **Speech-to-Text & Text-to-Speech:** Real-time speech interaction supported through browser Web Speech API or base64 audio streams using Twilio, Deepgram, and ElevenLabs.
*   **Dynamic Ticket Rendering:** Renders beautiful, real-time physical train tickets directly on the dashboard when bookings or status checks complete.
*   **Live Train Search Carousel:** Interactive cards showing top train suggestions, seat availabilities, prices, and classes (e.g. SL, 3A, CC).
*   **Automated Evaluation Simulator:** Integrated offline and online regression simulators measuring intent accuracy, slot filling rate, and latency percentiles (p50, p90, p99).
*   **Real-time Analytics Dashboard:** Aggregated call statistics, system configuration managers, and historical call transcription logs.

---

## 🛠️ System Architecture

```mermaid
graph TD
    User([User Call / Browser]) <--> |WebSocket / WebRTC| FastAPI[FastAPI Server]
    FastAPI <--> |FSM Coordinator| FSM[Finite State Machine]
    FSM <--> |Extract & Predict| LLM[Groq LLM / Llama 3.1]
    FSM <--> |Fallback Engine| Fallback[Local Rule-Based Classifier]
    FSM <--> |Search & Book| IRCTC[ConfirmTkt IRCTC API]
    FSM --> |Confirmations| SMS[Twilio SMS Outbox]
    FastAPI <--> |JSON APIs| Frontend[React / Vite Dashboard]
```

### 1. Dialog State Machine (FSM)
Governs conversation flow securely across these states:
- `GREET`: Initial welcome and language selection prompt.
- `LANGUAGE`: Detects language preferences (Hindi, English, Hinglish) or bypasses if a direct request is made.
- `INTENT`: Classifies user intent (Find Trains, Book Ticket, Check Seats, Cancel Ticket, Get PNR, End Call).
- `COLLECT`: Iteratively prompts the user for missing slot values with context-aware dialect-matched questions.
- `CONFIRM`: Reads back slot details and asks for final confirmation before triggering actions.
- `EXECUTE`: Runs backend APIs and sends SMS confirmations.
- `END`: Graceful exit and greeting teardown.

### 2. High-Performance LLM Brain
- **Intent & Slot Extraction:** Translates free-form speech transcripts into JSON payloads.
- **Context Injection:** Injects real-time train lists and seat status parameters into prompt boundaries.
- **Token Optimization:** Strips heavy raw nested JSON objects (`raw_train_data`) to prevent context limits, saving **~95%** of token footprint per turn.

---

## 📊 Measured Metrics & Evaluation Results

LocoVoice contains a built-in automated test simulator running across standard target booking/search scenarios.

### 1. Offline Mode (Local Rule-Based Parser)
*   **Total Test Cases:** 4
*   **Task Success Rate:** 100.00%
*   **Avg Slot Accuracy:** 100.00%
*   **p50 Latency:** 0.00ms (Immediate local parsing)
*   **p90 Latency:** ~480ms
*   **p99 Latency:** ~760ms

### 2. Online Mode (Groq Llama 3.1 8B API)
*   **Total Test Cases:** 4
*   **Task Success Rate:** 100.00%
*   **Avg Slot Accuracy:** 100.00%
*   **p50 Latency:** ~1,710ms (Real-world API network roundtrip)
*   **p90 Latency:** ~2,010ms
*   **p99 Latency:** ~2,010ms

---

## 📂 Project Structure

```
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── audio/            # Audio transcription / synthesis integrations
│   │   ├── brain/            # Dialog FSM & Groq LLM logic
│   │   ├── routers/          # FastAPI REST & WebSocket endpoints
│   │   ├── tools/            # IRCTC API integration & Twilio SMS outbox
│   │   ├── config.py         # Config managers
│   │   ├── database.py       # SQLite database initialization
│   │   └── models.py         # SQLAlchemy schemas
│   ├── config.json           # API Keys & Local Settings (masked)
│   ├── requirements.txt      # Python Dependencies
│   └── run.py                # Server entry point
├── frontend/                 # React Vite Client
│   ├── src/
│   │   ├── components/       # Settings, WebRTCTerminal, Logger, EvalRunner
│   │   ├── App.jsx           # Main Dashboard Shell
│   │   └── index.css         # Styling system
├── eval/                     # Evaluation & Regression Testing
│   ├── baselines/            # Evaluation benchmarks
│   ├── dataset.json          # Regression test scenarios
│   └── run_eval.py           # Evaluation runner script
```

---

## ⚙️ Setup and Installation

### Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your API keys in `config.json` (or use environment variables):
   ```json
   {
       "groq_api_key": "your_groq_key",
       "deepgram_api_key": "your_deepgram_key",
       "elevenlabs_api_key": "your_elevenlabs_key"
   }
   ```
4. Launch the backend server:
   ```bash
   python run.py
   ```

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
