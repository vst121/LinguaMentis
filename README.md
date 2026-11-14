# LinguaMentis

> **Think through language.**

LinguaMentis is a gamified AI debate experience for **B2/C1 German learners**.

It combines **German language development** with **structured thinking** using Edward de Bono's **Six Thinking Hats**.

Instead of following traditional language lessons, users enter a **MindQuest** — an intellectual challenge where they explore a complex topic from different perspectives and express their thoughts in German.

## Project Overview

LinguaMentis is a full-stack web application built around a gamified, AI-driven debate experience for B2/C1 German learners. The system combines structured thinking methods (Edward de Bono's Six Thinking Hats) with language practice, enabling users to explore complex topics in German through guided MindQuests.

The project consists of three main layers:

- **Frontend** (Next.js/TypeScript) — the interactive web interface for learners
- **Backend** (Python/FastAPI) — the application core managing MindQuest lifecycle, Six Hat agents, independent evaluation, and persistence
- **AI Layer** (Google Gemini) — provides structured intelligence for challenges, evaluations, and reflections

Key principles across the entire project:

- The application owns all state; AI provides intelligence, not control
- Thinking quality and German quality are evaluated independently and never combined
- Evidence accompanies every meaningful evaluation
- V1 focuses on a complete, high-quality vertical slice before adding infrastructure complexity

---

## Core Experience

```text

Think
  ↓
Express
  ↓
Challenge
  ↓
Evaluate
  ↓
Improve

```

A MindQuest follows this flow:

```text

Choose Topic
     ↓
Blue Agent
     ↓
Six Thinking Hats
     ↓
User responds in German
     ↓
Thinking Evaluation + German Evaluation
     ↓
Evidence + Feedback
     ↓
Next Challenge
     ↓
Final Reflection

```

---

## Six Thinking Hats

| Hat | Focus |

| --------- | --------------------------------------- |

| ⚪ White | Facts, information, evidence |

| 🔴 Red | Feelings, intuition, reactions |

| ⚫ Black | Risks, weaknesses, consequences |

| 🟡 Yellow | Benefits, opportunities, value |

| 🟢 Green | Creativity, alternatives, possibilities |

| 🔵 Blue | Process, orchestration, reflection |

The **Blue Agent** orchestrates the MindQuest and produces the final reflection.

---

## Two Independent Evaluations

Every response is evaluated in two separate dimensions:

### Thinking Quality

- Hat adherence

- Reasoning

- Depth

- Relevance

- Specificity

- Critical thinking

- Creativity where appropriate

### German Quality

- Grammar

- Vocabulary

- Sentence structure

- Naturalness

- Fluency

- B2/C1 appropriateness

The two scores are **never combined into a single score**.

Every important evaluation also provides **evidence** explaining the score.

---

## Architecture

LinguaMentis uses a **modular monolith** for V1.

```text

Next.js
   │
   ▼
FastAPI
   │
   ▼
MindQuest Engine
   │
   ├── Six Hat Agents
   │
   ├── Thinking Evaluator
   ├── German Evaluator
   │
   ▼
AI Gateway
   │
   ▼
Google Gemini
   │
   ▼
PostgreSQL

```

The key architectural principle is:

> **The application owns the state. AI provides intelligence, not application control.**

---

## Technology Stack

### Backend

- Python 3.12

- FastAPI

- SQLAlchemy 2.x

- Alembic

- PostgreSQL

- Pydantic

### Frontend

- Next.js

- TypeScript

- React

- Tailwind CSS

### AI

- Google Gemini

- Structured LLM outputs

- Configurable models

### Development

- uv

- Docker Compose

- pytest

---

## Project Structure

```text
linguamentis/
├── .devcontainer/
│   ├── Dockerfile
│   ├── devcontainer.json
│   └── docker-compose.yml
├── backend/
│   ├── src/linguamentis/
│   │   ├── agents/
│   │   ├── ai/
│   │   ├── api/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── shared/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── services/
│   │   └── types/
│   └── tests/
├── docs/
│   ├── PRD.md
│   ├── Architecture.md
│   ├── HatContracts.md
│   └── EvaluationRubric.md
├── scripts/
│   └── dev.sh
└── Makefile
```

---

## V1 Scope

The first version focuses on:

- Text-based MindQuests

- Six Thinking Hats

- Blue Agent orchestration

- Independent Thinking evaluation

- Independent German evaluation

- Evidence-based feedback

- Persistent learning history

- Final MindQuest reflection

- Basic gamification

### Not in V1

- Authentication

- Mobile application

- Voice interaction

- Kafka

- Microservices

- Redis

- Celery

- Vector database

- Event sourcing

- Payments

The goal is to build a **complete, high-quality vertical slice before adding infrastructure complexity**.

---

## First Vertical Slice

Development starts with a complete **Black Hat MindQuest**:

```text

Blue Agent
    ↓
Topic
    ↓
Black Hat Agent
    ↓
Challenge
    ↓
User Response
    ↓
Thinking Evaluator
    +
German Evaluator
    ↓
Evidence
    ↓
Feedback
    ↓
Next Challenge
    ↓
Final Reflection

```

Once this flow works end-to-end, the remaining hats can be added.

---

## Development (Dev Container)

LinguaMentis uses a **VS Code Dev Container** as the standard development environment (`.devcontainer/`). It provides Python 3.12, `uv`, Node.js, `pnpm`, and a dedicated PostgreSQL 17 service (`postgres:5432`) out of the box.

1. Open the repository in VS Code and run **Dev Containers: Reopen in Container**.
2. Set `GEMINI_API_KEY` in `backend/.env` (created automatically from `backend/.env.example`).
3. Start both Backend (`http://localhost:8000`) and Frontend (`http://localhost:3000`):

```bash
make dev
# or: ./scripts/dev.sh
```

---

## End User

LinguaMentis is designed for **B2/C1 German learners** who want to develop their thinking and language skills through structured intellectual exploration.

### What the End User Gets

- **MindQuests** — intellectual challenges on complex topics explored through the Six Thinking Hats
- **Real-time AI-guided challenges** — a Blue Agent orchestrates each session, presenting tailored prompts at each Hat
- **Independent evaluations** — separate scores for Thinking Quality and German Quality with detailed evidence
- **German corrections** — actionable, concise corrections with explanations
- **Final Reflection** — a comprehensive summary of thinking and German performance at the end of each MindQuest
- **Learning journey** — progress tracking across completed MindQuests

### What the End User Needs

To use LinguaMentis, the end user needs:

- A modern web browser (desktop recommended for the V1 experience)
- A stable internet connection (the application communicates with AI services via the backend)
- No local installation of Python, Node.js, or any development tools
- No API keys or configuration — all infrastructure is handled server-side

### What the End User Does

1. Choose or be assigned a topic
2. Follow the Blue Agent's guidance through each Thinking Hat
3. Respond to challenges in German
4. Receive independent Thinking and German evaluations with evidence and feedback
5. Continue through all six Hats
6. Review the final reflection and track their learning progress

---

## Environment Variables

Create a `.env` file for the backend.

```env
DATABASE_URL=postgresql+asyncpg://linguamentis:linguamentis@postgres:5432/linguamentis
GEMINI_API_KEY=your-gemini-api-key

AI_MODEL_BLUE=gemini-2.5-flash
AI_MODEL_HAT=gemini-2.5-flash
AI_MODEL_THINKING_EVALUATOR=gemini-2.5-flash
AI_MODEL_GERMAN_EVALUATOR=gemini-2.5-flash
AI_MODEL_REFLECTION=gemini-2.5-flash
```

The Gemini API key is **server-side only** and must never be exposed to the frontend. Model
settings must contain Gemini model IDs, not API keys.

---

## Testing & Quality Checks

Run all unit, component, and integration tests across Backend and Frontend:

```bash
make test
```

Individual test and lint targets:

```bash
make test-backend   # Backend unit, integration & offline evaluation dataset tests (pytest)
make test-frontend  # Frontend unit, component & page tests (Vitest + React Testing Library)
make test-e2e       # End-to-end browser tests across Next.js & FastAPI (Playwright)
make test-eval      # Opt-in live Gemini evaluation regression harness
make lint           # Backend (ruff) + Frontend (ESLint & TypeScript) checks
```

---

## Product Philosophy

LinguaMentis should not become:

> A German-learning chatbot with AI features.

It should become:

> **An intellectual experience where German is the language through which users learn to think, argue, question, and express ideas.**

---

## License

TBD
