# LinguaMentis

> **Think through language.**

LinguaMentis is a gamified, AI-assisted German debate and reasoning platform built for **B2 and C1 German learners**. It pairs Edward de Bono's **Six Thinking Hats** methodology with independent dual evaluation, elaborated language propositions, and real-time voice interaction so learners practice expressing nuanced ideas in natural, high-level German.

---

## Table of Contents

- [Key Capabilities](#key-capabilities)
- [Debate & Interaction Modes](#debate--interaction-modes)
  - [1. Answering Mode](#1-answering-mode)
  - [2. Argue Mode (Perspective Challenger)](#2-argue-mode-perspective-challenger)
  - [3. Written & Spoken Voice Experience](#3-written--spoken-voice-experience)
- [Six Thinking Hats](#six-thinking-hats)
- [Evaluation, Radar Analytics & Elaborated Propositions](#evaluation-radar-analytics--elaborated-propositions)
- [Performance & Latency Optimizations](#performance--latency-optimizations)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Option A: VS Code Dev Container (Recommended)](#option-a-vs-code-dev-container-recommended)
  - [Option B: Local Setup](#option-b-local-setup)
- [Environment Variables](#environment-variables)
- [REST API Overview](#rest-api-overview)
- [Testing, Linting & Benchmarks](#testing-linting--benchmarks)
- [Documentation](#documentation)
- [Product Philosophy](#product-philosophy)
- [License](#license)

---

## Key Capabilities

- **Dual Debate Modes (`Answering Mode` & `Argue Mode`)**: Choose between guided sequential exploration across all six hats or adversarial *Perspective Challenger* debates with custom dark/slate styling and level-calibrated pass thresholds.
- **Independent Thinking & German Evaluation**: Every submission is scored concurrently on **5 Thinking dimensions** and **5 German language dimensions**—never collapsed into a single blended score—backed by concrete evidence quotes and selective corrections.
- **Aligned Elaborated Response Propositions (`Sprach-Upgrade`)**: Alongside each evaluation, an AI-crafted rewrite expresses the learner's *exact* stance and reasoning at a stronger B2/C1 level, with interactive inline highlights categorized by `Wortschatz` (vocabulary), `Satzbau` (syntax), `Redemittel` (idioms), `Präzision` (precision), and `Konnektor` (connectors).
- **Interactive Radar Charts**: 5-axis SVG radar visualizations (`ScoreRadarChart`) display Thinking and German dimension breakdowns across every turn evaluation, final reflection, and the cumulative Learning Profile.
- **Voice Dictation & Spoken Conversation Mode**: Switch seamlessly between typing (`Eintippen`), live voice dictation (`Einsprechen` with Web Speech API + Gemini audio transcription fallback), and full hands-free spoken debate (`Gesprächsmodus` with Gemini TTS audio playback and silence detection).
- **Persistent Journey & Full Quest Lifecycle**: Create quests with topic validation, delete individual quests from the dashboard, resume answered turns seamlessly without losing evaluations, and track long-term growth on `/learning` and `/history`.

---

## Debate & Interaction Modes

When creating a MindQuest on `/mindquests`, learners select a **Topic** (validated for at least 3 characters), **Language Level** (`B2` or `C1`), and **Mode**:

### 1. Answering Mode

- **Light theme** interface for focused, structured exploration.
- **Immediate Start**: Opens directly on the first Thinking Hat question without an intermediate "ready" screen.
- **Single Round per Hat**: Each color consists of one focused challenge and one evaluated response across the mandatory 6-hat sequence:
  `WHITE → YELLOW → GREEN → RED → BLACK → BLUE`.
- **Resilient State Recovery**: Reopening a MindQuest whose active turn has already been answered automatically restores the saved evaluations, radar charts, and `Sprach-Upgrade` proposition.

### 2. Argue Mode (Perspective Challenger)

- **Lightened Slate/Indigo Dark Theme**: Automatically switches the entire application shell, cards, radar charts, and reflections to a readable slate dark theme with zero red accents.
- **Learner-First Layout**: The learner presents their argument on the **left** while the **Perspective Challenger** responds, counter-argues, and evaluates on the **right**, with top-right sticky action buttons (`Antwort überarbeiten` / `Nächste Perspektive`) always within reach.
- **Flexible Hat Switching with State Preservation**: Top-left interactive hat badges represent each hat's status (**completed**, **active**, **open**, **locked**). Learners can freely switch between incomplete hats mid-debate; drafts, turns, and prior counter-arguments are preserved when returning.
- **Read-Only Solved Hats**: Once a hat passes its threshold, it cannot be edited further, but clicking it opens a read-only inspection view (`Abgeschlossen · Nur Ansicht`) displaying the final response, scores, radar charts, and `Sprach-Upgrade`.
- **Level-Calibrated Pass Thresholds**:
  - **B2**: Requires a mean score of **`≥ 10 %`** across all 10 evaluation dimensions.
  - **C1**: Requires strictly **`> 80 %`** across all 10 evaluation dimensions.
  - Below the threshold, the **Perspective Challenger** rejects the argument with a targeted counter-argument and improvement directive so the learner can refine and resubmit.
- **Mandatory Final Blue Hat**: The **Blue Hat** badge is always visible in the bar and selection grid as locked (`Letzter Schritt`). Selecting it early displays an explicit reminder that Blue Hat synthesis must always come last; once the first 5 hats are completed, Blue Hat unlocks for the final synthesis round (1 round) before transitioning to the Final Reflection.

### 3. Written & Spoken Voice Experience

Both **Answering Mode** and **Argue Mode** support:

- **Written + Voice Dictation (`Schriftlich`)**: Toggle between `Eintippen` (keyboard) and `Einsprechen` (microphone capture with live audio-level bars, elapsed timer, interim transcripts, and server-side `/api/v1/speech/transcribe` fallback).
- **Spoken Conversation (`Gesprächsmodus`)**: Full duplex-style audio loop via `POST /api/v1/mindquests/{id}/conversation/opening` and `/conversation/turn` with live silence auto-submit, TTS audio playback (`/api/v1/speech/synthesize`), and Perspective Challenger audio feedback in Argue Mode.

---

## Six Thinking Hats

| Hat | German Name | Cognitive Focus |
| --- | --- | --- |
| ⚪ White | Weißer Hut | Facts, verified information, assumptions vs. evidence, unknowns |
| 🟡 Yellow | Gelber Hut | Benefits, opportunities, positive consequences, practical value |
| 🟢 Green | Grüner Hut | Creativity, alternatives, unconventional possibilities |
| 🔴 Red | Roter Hut | Intuition, emotions, immediate personal reactions |
| ⚫ Black | Schwarzer Hut | Risks, weaknesses, failure modes, second-order consequences |
| 🔵 Blue | Blauer Hut | Process orchestration, cross-hat synthesis, final reflection |

Every hat operates under a strict application-owned **Hat Contract** (`backend/src/linguamentis/domain/hats/contracts.py`) so the LLM never redefines hat boundaries or owns state transitions.

---

## Evaluation, Radar Analytics & Elaborated Propositions

1. **Deterministic Scoring**: The LLM outputs raw per-dimension scores (`0–100`) plus concrete `Evidence` items. Final aggregate scores and anchors (`90–100` Excellent, `80–89` Strong, etc.) are computed deterministically by domain formulas:
   - **Thinking Quality**: `hat_adherence` (30%), `relevance` (15%), `reasoning` (25%), `depth` (15%), `specificity` (15%).
   - **German Quality**: `grammar` (25%), `vocabulary` (20%), `sentence_structure` (20%), `naturalness` (20%), `level_appropriateness` (15%).
2. **Radar Visualizations**: Clean 5-axis SVG radar charts without visual clutter render Thinking and German metrics across turn feedback, Final Reflection (`/mindquests/{id}/reflection`), and Learning Profile (`/learning`).
3. **`Sprach-Upgrade` Propositions**: Persisted in PostgreSQL (`response_propositions`), providing an aligned B2/C1 model rewrite of the user's answer with interactive numbered `<mark>` spans linked to comparative `original → upgrade` cards.

---

## Performance & Latency Optimizations

- **Overlapped Parallel AI Execution**: Inside `TurnService.submit_response`, `ResponseProposition` generation is launched immediately alongside `evaluate_thinking`, `evaluate_german`, and optional Jev adherence verification (`asyncio.gather`), overlapping with `HatFeedback` and follow-up generation so the elaborated rewrite adds negligible wait time.
- **Instant Hat Selection in Argue Mode**: Opening prompts for the 5 selectable hats are served immediately (`~40 ms` locally) without blocking on an initial LLM round-trip.
- **Speculative Prefetching**: `ChallengePrefetchCache` warms the next Hat Challenge (including the final Blue Hat prompt after the 5th Argue Hat) and the Final Reflection while the learner reads their feedback.
- **Gemini Connection Warmup & Keep-Alive**: Shared `httpx.AsyncClient` connection pooling with background TLS warmup on FastAPI startup and fallback model support (`AI_MODEL_STRUCTURED_FALLBACK`).
- **Explicit Loading Feedback**: Live elapsed-second counters (`1s, 2s…`), spinner cards, and sticky progress banners keep learners informed during every AI operation.

---

## Architecture

LinguaMentis is structured as a **Clean / Modular Monolith** where **the application owns all state** and AI acts purely as a structured capability behind `AIGateway`.

```text
┌──────────────────────────────────────────────────────────┐
│                  Frontend (Next.js 15)                   │
│  /  ·  /mindquests  ·  /mindquests/[id]  ·  /reflection  │
│  /learning          ·  /history                          │
└────────────────────────────┬─────────────────────────────┘
                             │ HTTP (/api/v1 proxy)
                             ▼
┌──────────────────────────────────────────────────────────┐
│                 Backend API (FastAPI)                    │
│  mindquests  ·  conversation  ·  learning  ·  speech     │
└────────────────────────────┬─────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   Application Services                   │
│  MindQuestService · TurnService · EvaluationService      │
│  ConversationService · LearningService · PrefetchCache   │
└──────────────┬─────────────────────────────┬─────────────┘
               ▼                             ▼
┌──────────────────────────────┐ ┌─────────────────────────┐
│     Pure Domain Layer        │ │   AI & Agents Layer     │
│  MindQuest State Machine     │ │  6 Hat Agents +         │
│  Hat Contracts & Scoring     │ │  ConversationAgent      │
│  Evaluations & Propositions  │ │  AIGateway -> Gemini    │
└──────────────┬───────────────┘ └─────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────────┐
│        Infrastructure (Async SQLAlchemy + Postgres)      │
│  users, mind_quests, hat_rounds, turns,                  │
│  thinking_evaluations, german_evaluations, evidence,     │
│  response_propositions, final_reflections,               │
│  user_activities                                         │
└──────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technologies |
| --- | --- |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, Pydantic Settings, SQLAlchemy 2.x (`asyncpg`), Alembic, `httpx`, `structlog`, `uv` |
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript 5.7, Tailwind CSS 3 (`class` dark mode), `lucide-react`, `pnpm` |
| **Database** | PostgreSQL 17 (SQLite `aiosqlite` in automated tests) |
| **AI Capabilities** | Google Gemini (`generateContent` structured JSON schemas, audio transcription, TTS synthesis), optional Jev adherence verifier |
| **Quality & Testing** | `pytest`, `pytest-asyncio`, `ruff`, `vitest`, Testing Library, `eslint`, `tsc`, Playwright |

---

## Project Structure

```text
LinguaMentis/
├── .devcontainer/               # VS Code Dev Container + PostgreSQL 17 setup
├── backend/
│   ├── alembic/                 # Database migration setup
│   ├── src/linguamentis/
│   │   ├── agents/              # 6 Hat agents, ConversationAgent, AgentRegistry
│   │   ├── ai/                  # AIGateway, GeminiClient, prompts, structured schemas, Jev
│   │   ├── api/v1/              # FastAPI routers (mindquests, conversation, learning, speech)
│   │   ├── application/         # MindQuestService, TurnService, EvaluationService, ConversationService, LearningService
│   │   ├── domain/              # Pure domain entities, state machine, HatContracts, scoring, propositions
│   │   ├── infrastructure/      # Settings, async SQLAlchemy models & repositories
│   │   └── shared/              # Domain exceptions, structured logging, Result helpers
│   └── tests/                   # unit/, integration/, performance/, evaluation/, e2e_server.py
├── frontend/
│   ├── src/
│   │   ├── app/                 # /, /mindquests, /mindquests/[id], /reflection, /learning, /history
│   │   ├── components/          # evaluation (Radar, Proposition), conversation, speech, hats, layout, ui
│   │   ├── hooks/               # useConversationSession, useSpeechToText
│   │   ├── services/api/        # Typed API client & domain endpoint wrappers
│   │   └── types/               # TypeScript DTOs matching backend contracts
│   └── tests/                   # unit/, components/, pages/, performance/, e2e/ (Playwright)
├── docs/                        # Architecture.md, EvaluationRubric.md, HatContracts.md, PRD.md
├── scripts/
│   ├── dev.sh                   # Unified Dev Container startup & process supervisor
│   └── benchmark_live.py        # End-to-end latency profiler against PostgreSQL & Gemini
└── Makefile                     # Common dev, test, lint, speed, and benchmark commands
```

---

## Getting Started

### Option A: VS Code Dev Container (Recommended)

The repository includes a preconfigured VS Code Dev Container (`.devcontainer/`) with Python, `uv`, Node.js, `pnpm`, and PostgreSQL 17.

1. Open the project in VS Code and run **Dev Containers: Reopen in Container**.
2. Add your Gemini API key to `backend/.env` (auto-copied from `backend/.env.example`):
   ```env
   GEMINI_API_KEY=your-real-gemini-api-key
   ```
3. Launch both Backend (`http://localhost:8000`) and Frontend (`http://localhost:3000`):
   ```bash
   make dev
   # or directly: ./scripts/dev.sh
   ```

### Option B: Local Setup

**Prerequisites**: Python 3.12+, [`uv`](https://docs.astral.sh/uv/), Node.js 20+, `pnpm` (or `corepack pnpm`), and a running PostgreSQL instance.

1. **Configure Backend**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your DATABASE_URL and GEMINI_API_KEY
   uv sync --extra dev
   uv run alembic upgrade head
   uv run python -m uvicorn linguamentis.main:app --host 127.0.0.1 --port 8000
   ```
2. **Start Frontend** (in a second terminal):
   ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```
3. Open **http://localhost:3000** in your browser (FastAPI Swagger docs are available at **http://127.0.0.1:8000/docs**).

---

## Environment Variables

Backend configuration is managed via `backend/.env` (`backend/src/linguamentis/infrastructure/configuration.py`):

| Variable | Default / Example | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://linguamentis:linguamentis@postgres:5432/linguamentis` | Async SQLAlchemy connection string |
| `GEMINI_API_KEY` | *(required, server-side only)* | Google Gemini API key (never exposed to frontend) |
| `GEMINI_BASE_URL` | `https://generativelanguage.googleapis.com` | Gemini API base URL |
| `AI_MODEL_BLUE` | `gemini-2.5-flash` | Model used for Blue Hat synthesis challenges |
| `AI_MODEL_HAT` | `gemini-2.5-flash` | Model used for Hat challenges, feedback, propositions, and Argue rejections |
| `AI_MODEL_THINKING_EVALUATOR` | `gemini-2.5-flash` | Model used for Thinking Quality scoring |
| `AI_MODEL_GERMAN_EVALUATOR` | `gemini-2.5-flash` | Model used for German Quality scoring & corrections |
| `AI_MODEL_REFLECTION` | `gemini-2.5-flash` | Model used for Blue Agent Final Reflection |
| `AI_MODEL_TRANSCRIPTION` | `gemini-2.5-flash` | Model used for server-side German speech transcription |
| `AI_MODEL_CONVERSATION` | `gemini-2.5-flash` | Model used for spoken Conversation replies |
| `AI_MODEL_TTS` | `gemini-3.8-flash-lite-tts` | Model used for German speech synthesis |
| `AI_TTS_VOICE` | `Kore` | Voice preset for Gemini TTS |
| `AI_MODEL_STRUCTURED_FALLBACK` | `gemini-2.5-flash` | Fallback model when structured JSON parsing fails |
| `AI_REQUEST_TIMEOUT_SECONDS` | `120` | Upstream AI request timeout |
| `AI_MAX_RETRIES` | `2` | Retry count for transient HTTP/parsing errors |
| `JEV_ENABLED` | `false` | Optional external Jev hat-adherence verifier (`JEV_API_KEY`, `JEV_BASE_URL`) |
| `DEFAULT_USER_ID` | `00000000-0000-0000-0000-000000000001` | Pre-seeded V1 learner ID |

---

## REST API Overview

All endpoints are served under `/api/v1` (plus `GET /health`):

| Endpoint | Purpose |
| --- | --- |
| `POST /api/v1/mindquests` | Create a MindQuest (`topic`, `target_level`, `mode`: `ANSWERING` \| `ARGUE`) |
| `GET /api/v1/mindquests` | List user MindQuests |
| `GET /api/v1/mindquests/{id}` | Retrieve MindQuest state, rounds, and turns |
| `DELETE /api/v1/mindquests/{id}` | Delete a MindQuest and its cascaded rounds, evaluations, propositions, and activities |
| `POST /api/v1/mindquests/{id}/start` | Start an Answering Mode MindQuest on the White Hat |
| `POST /api/v1/mindquests/{id}/select-hat` | Select or switch hats in Argue Mode (restores incomplete state or returns read-only solved scores; enforces Blue last) |
| `POST /api/v1/mindquests/{id}/responses` | Submit a German response -> returns Thinking & German evaluations, feedback, `Sprach-Upgrade` proposition, average score, and next challenge if applicable |
| `GET /api/v1/mindquests/{id}/current-evaluation` | Restore persisted evaluations/proposition for an already-answered active turn |
| `POST /api/v1/mindquests/{id}/advance` | Advance to the next hat or complete the MindQuest with Final Reflection |
| `GET /api/v1/mindquests/{id}/reflection` | Retrieve the Final Reflection and single-quest radar metrics |
| `POST /api/v1/mindquests/{id}/conversation/opening` | Open spoken conversation mode and synthesize initial German audio |
| `POST /api/v1/mindquests/{id}/conversation/turn` | Process spoken audio/transcript turn and return spoken reply + evaluations |
| `POST /api/v1/speech/transcribe` | Transcribe German audio (`audio/webm`, `ogg`, `mp4`, `wav`, `mp3`) |
| `POST /api/v1/speech/synthesize` | Synthesize German text-to-speech (`audio/wav`) |
| `GET /api/v1/users/{user_id}/learning-profile` | Aggregated Thinking & German profile metrics |
| `GET /api/v1/users/{user_id}/activities` | Chronological user activity log |
| `GET /api/v1/users/{user_id}/mindquests` | List MindQuests for a specific user |

---

## Testing, Linting & Benchmarks

Run the full automated suite across backend and frontend:

```bash
make test
```

Individual targets defined in `Makefile`:

```bash
make test-backend    # Backend unit, integration, performance & offline evaluation tests (pytest)
make test-frontend   # Frontend unit, component, page & speed tests (Vitest + Testing Library)
make test-speed      # Deterministic parallelism, prefetch & SQL query-count tests
make test-e2e        # End-to-end browser journey & latency budgets (Playwright)
make test-eval       # Opt-in live Gemini evaluation regression harness (RUN_AI_EVALUATION=1)
make benchmark-live  # Step-by-step live latency profiler against PostgreSQL & Gemini
make lint            # Backend ruff check + Frontend ESLint & TypeScript (tsc --noEmit)
make clean           # Remove temporary test, lint, and build caches
```

---

## Documentation

Additional design and specification documents are available in `docs/`:

- [`docs/PRD.md`](docs/PRD.md) — Product requirements and V1 scope
- [`docs/Architecture.md`](docs/Architecture.md) — Modular monolith design, state ownership, and boundaries
- [`docs/HatContracts.md`](docs/HatContracts.md) — Behavioral contracts for all Six Thinking Hats
- [`docs/EvaluationRubric.md`](docs/EvaluationRubric.md) — Independent Thinking and German scoring rubrics

---

## Product Philosophy

LinguaMentis should never be just a generic language chatbot. It is designed to be:

> **An intellectual experience where German is the medium through which learners think critically, argue persuasively, question assumptions, and express nuanced ideas.**

---

## License

TBD

