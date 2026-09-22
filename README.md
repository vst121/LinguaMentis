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
- **AI Layer** (OpenRouter) — provides structured intelligence for challenges, evaluations, and reflections

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
OpenRouter
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

- OpenRouter

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
│
├── backend/
│   ├── src/
│   │   └── linguamentis/
│   │       ├── api/
│   │       ├── application/
│   │       ├── domain/
│   │       ├── agents/
│   │       ├── ai/
│   │       └── infrastructure/
│   │
│   └── tests/
│
├── frontend/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── services/
│       └── types/
│
├── docs/
│   ├── PRD.md
│   ├── Architecture.md
│   ├── HatContracts.md
│   ├── EvaluationRubric.md
│   └── AIContracts.md
│
└── docker-compose.yml

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

## Running Locally

### Backend

```bash

cd backend

uv sync

uv run uvicorn linguamentis.main:app --reload

```

### Frontend

```bash

cd frontend

npm install

npm run dev

```

### Database

PostgreSQL can be started with:

```bash

docker compose up -d postgres

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

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5438/linguamentis

OPENROUTER_API_KEY=your-api-key

OPENROUTER_BASE_URL=https://openrouter.ai/api/v1



AI_MODEL_BLUE=...

AI_MODEL_HAT=...

AI_MODEL_THINKING_EVALUATOR=...

AI_MODEL_GERMAN_EVALUATOR=...

AI_MODEL_REFLECTION=...

```

The OpenRouter API key is **server-side only** and must never be exposed to the frontend.

---

## Testing

Run unit and integration tests:

```bash

cd backend

uv run pytest

```

AI evaluation tests are kept separately:

```text

backend/tests/evaluation/

```

These will eventually provide a regression harness for comparing prompts, models, and evaluator quality.

---

## Product Philosophy

LinguaMentis should not become:

> A German-learning chatbot with AI features.

It should become:

> **An intellectual experience where German is the language through which users learn to think, argue, question, and express ideas.**

---

## License

TBD
