# LinguaMentis Backend

> **Think through language.**

The LinguaMentis backend is the application core responsible for MindQuest lifecycle management, Six Thinking Hats orchestration, independent evaluation, learning history, and persistence.

It is intentionally designed as a **modular monolith** with an AI-native architecture.

The backend owns application state.

The LLM does not.

---

## Architecture

```text

                   ┌─────────────────────┐
                   │     Next.js App     │
                   └──────────┬──────────┘
                              │ HTTP
                              ▼
                   ┌─────────────────────┐
                   │      FastAPI        │
                   │        API          │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │    Application      │
                   │      Services       │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │       Domain        │
                   │ MindQuest + Hats    │
                   │ Evaluation + Users  │
                   └──────────┬──────────┘
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
      ┌───────────────┐                 ┌───────────────┐
      │ Infrastructure│                 │ AI / Agents   │
      │ PostgreSQL    │                 │               │
      │ SQLAlchemy    │                 │ Hat Agents    │
      │ Alembic       │                 │ Evaluators    │
      └───────────────┘                 │ LLM Gateway   │
                                        └───────┬───────┘
                                                │
                                                ▼
                                        ┌───────────────┐
                                        │  OpenRouter   │
                                        └───────────────┘

```

### Architectural rule

> **LinguaMentis is an AI-enabled application, not an LLM-controlled application.**

The application owns:

- MindQuest state

- current Hat

- turns

- responses

- evaluations

- scores

- persistence

- learning history

- completion

AI provides:

- challenges

- questions

- evaluations

- feedback

- recommendations

- final reflection

---

## Technology Stack

| Area              | Technology     |
| ----------------- | -------------- |
| Language          | Python 3.12    |
| API               | FastAPI        |
| ORM               | SQLAlchemy 2.x |
| Database          | PostgreSQL     |
| Migrations        | Alembic        |
| AI Gateway        | OpenRouter     |
| Validation        | Pydantic       |
| Package Manager   | uv             |
| Testing           | pytest         |
| Async             | asyncio        |
| Local Environment | Docker Compose |

---

## Project Structure

```text

backend/

├── pyproject.toml
├── uv.lock
├── .env.example
├── README.md
│
├── src/
│   └── linguamentis/
│       ├── main.py
│       │
│       ├── api/
│       │   ├── dependencies.py
│       │   ├── router.py
│       │   └── v1/
│       │       ├── mindquests.py
│       │       ├── turns.py
│       │       ├── evaluations.py
│       │       ├── users.py
│       │       └── learning.py
│       │
│       ├── application/
│       │   ├── mindquests/
│       │   │   ├── commands.py
│       │   │   ├── queries.py
│       │   │   └── service.py
│       │   ├── turns/
│       │   │   └── service.py
│       │   ├── evaluation/
│       │   │   └── service.py
│       │   └── learning/
│       │       └── service.py
│       │
│       ├── domain/
│       │   ├── users/
│       │   ├── mindquests/
│       │   ├── hats/
│       │   ├── evaluations/
│       │   └── learning/
│       │
│       ├── agents/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── blue.py
│       │   ├── white.py
│       │   ├── red.py
│       │   ├── black.py
│       │   ├── yellow.py
│       │   └── green.py
│       │
│       ├── ai/
│       │   ├── client.py
│       │   ├── models.py
│       │   ├── prompts.py
│       │   ├── gateway.py
│       │   └── openrouter.py
│       │
│       ├── infrastructure/
│       │   ├── database/
│       │   │   ├── session.py
│       │   │   ├── models.py
│       │   │   └── repositories/
│       │   └── configuration.py
│       │
│       └── shared/
│           ├── exceptions.py
│           ├── logging.py
│           └── result.py
│
└── tests/
   ├── unit/
   ├── integration/
   └── evaluation/

```

---

# Domain

The domain contains the business concepts of LinguaMentis.

Important concepts include:

```text

User

MindQuest

HatRound

Turn

ThinkingEvaluation

GermanEvaluation

Evidence

FinalReflection

UserLearningProfile

```

The domain must not depend on:

- FastAPI

- SQLAlchemy

- PostgreSQL

- OpenRouter

- HTTP

- frontend code

---

# MindQuest

A `MindQuest` represents one complete intellectual exploration around a topic.

Example:

```text

MindQuest

   Topic:

   "Sollte KI in Unternehmen stärker reguliert werden?"

```

A MindQuest contains:

```text

MindQuest

├── HatRounds
│    └── Turns
│         └── Responses
│              ├── ThinkingEvaluation
│              └── GermanEvaluation
│                   └── Evidence
│
└── FinalReflection

```

---

# MindQuest Lifecycle

The application owns the lifecycle.

```text

CREATED
  ↓
TOPIC\_SELECTED
  ↓
IN\_PROGRESS
  ↓
HAT\_ACTIVE
  ↓
HAT\_COMPLETED
  ↓
ALL\_HATS\_COMPLETED
  ↓
FINAL\_EVALUATION
  ↓
COMPLETED

```

The LLM cannot transition the MindQuest between states.

The application decides when a state transition is valid.

---

# Six Thinking Hats

Each Hat Agent has a defined behavioral contract.

```text

White  → Information

Red    → Emotion / intuition

Black  → Risks / weaknesses

Yellow → Benefits / opportunities

Green  → Creativity / alternatives

Blue   → Process / orchestration

```

The canonical definitions are documented in:

```text

HatContracts.md

```

---

# Agents

Agents are responsible for interaction within a specific thinking perspective.

```text

AgentRegistry

     │
     ├── WhiteHatAgent
     ├── RedHatAgent
     ├── BlackHatAgent
     ├── YellowHatAgent
     ├── GreenHatAgent
     └── BlueHatAgent

```

Agents should:

- receive controlled context

- follow their Hat Contract

- generate structured challenges

- adapt to the learner's level

- maintain the assigned thinking perspective

Agents should not:

- own persistence

- control MindQuest state

- access repositories directly

- evaluate themselves

- communicate directly with OpenRouter

---

# Blue Agent

The Blue Agent is the orchestrator throughout the MindQuest.

Blue is responsible for:

- introducing the challenge

- coordinating Hats

- identifying gaps

- deciding when further exploration is useful

- coordinating transitions

- initiating final reflection

- synthesizing the MindQuest

Blue is **not** the application's state owner.

The `MindQuestEngine` / application layer remains responsible for lifecycle and state.

---

# AI Gateway

Agents communicate with the LLM through an abstraction.

```text

Agent
 ↓
ILLMClient
 ↓
LLM Gateway
 ↓
OpenRouterClient
 ↓
OpenRouter

```

Agents must not depend directly on OpenRouter.

This allows us to change:

- provider

- model

- prompting strategy

- retry strategy

- structured-output implementation

without changing domain or agent behavior.

---

# Structured AI Output

Important AI interactions use structured output.

Examples:

```text

HatChallenge

ThinkingEvaluation

GermanEvaluation

HatFeedback

FinalReflection

```

Example:

```python

class HatChallenge(BaseModel):

   question: str

   instruction: str

   expected\_thinking\_mode: HatType

   difficulty: int

```

Unstructured LLM responses should not be used for important application decisions.

---

# Independent Evaluation

Thinking and German are evaluated separately.

```text

Learner Response

      │
      ├───────────────┐
      ▼               ▼
ThinkingEvaluator   GermanEvaluator
      │               │
      ▼               ▼
Thinking Score      German Score
      │               │
      ▼               ▼
Evidence            Evidence

```

The backend must never collapse these into one "overall ability" score.

---

# Evaluation

The evaluation system follows:

```text

EvaluationRubric.md

```

Thinking evaluates:

- Hat adherence

- relevance

- reasoning

- depth

- specificity

German evaluates:

- grammar

- vocabulary

- sentence structure

- naturalness

- level appropriateness

Every meaningful evaluation should provide evidence.

---

# Persistence

PostgreSQL is the source of truth for the learner's journey.

The backend preserves:

- users

- MindQuests

- HatRounds

- turns

- responses

- thinking evaluations

- German evaluations

- evidence

- final reflections

- activities

Historical evaluation data should not be overwritten merely because a newer evaluation exists.

---

# Learning Profile

`UserLearningProfile` is derived from accumulated learning history.

It is not the source of truth.

```text

Responses
   ↓
Evaluations
   ↓
Evidence
   ↓
Historical Analysis
   ↓
UserLearningProfile

```

This allows the system to preserve the complete learning journey.

---

# API

Initial API surface:

```http

POST   /api/v1/mindquests

GET    /api/v1/mindquests

GET    /api/v1/mindquests/{id}



POST   /api/v1/mindquests/{id}/start

POST   /api/v1/mindquests/{id}/responses

POST   /api/v1/mindquests/{id}/advance



GET    /api/v1/mindquests/{id}/reflection



GET    /api/v1/users/{user\_id}/learning-profile

GET    /api/v1/users/{user\_id}/activities

GET    /api/v1/users/{user\_id}/mindquests

```

The API should expose use cases rather than internal implementation details.

---

# Error Handling

The API should provide consistent errors for:

- invalid MindQuest state

- invalid Hat transition

- missing MindQuest

- missing user

- invalid response

- AI provider failure

- evaluation failure

An AI failure must not cause loss of a learner response.

Preferred flow:

```text

Submit Response

     ↓

Persist Response

     ↓

Run Evaluations

     ↓

Persist Evaluation

```

The response should exist even if AI evaluation temporarily fails.

---

# Logging

Important operations should include structured metadata such as:

```text

request\_id

user\_id

mindquest\_id

hat

turn\_id

operation

model

evaluation\_type

latency

```

Do not log sensitive or unnecessary prompt/user data by default.

---

# Testing

Tests are organized into:

```text

tests/
├── unit/
├── integration/
└── evaluation/

```

## Unit tests

Focus on:

- domain rules

- state transitions

- Hat Contracts

- validation

- application services

## Integration tests

Focus on:

- PostgreSQL

- repositories

- API behavior

- MindQuest lifecycle

- persistence

## Evaluation tests

Focus on:

- evaluator consistency

- Hat adherence

- German correction quality

- score stability

- regression

---

# Local Development

## Requirements

Install:

- Python 3.12+

- uv

- Docker

- Docker Compose

---

## Install Dependencies

```bash

uv sync

```

---

## Environment Variables

Create:

```text

.env

```

based on:

```text

.env.example

```

Typical configuration:

```env

DATABASE\_URL=postgresql+asyncpg://linguamentis:linguamentis@localhost:5432/linguamentis



OPENROUTER\_API\_KEY=your-key



OPENROUTER\_MODEL=your-model

```

The exact model configuration should remain environment-driven.

---

## Start PostgreSQL

```bash

docker compose up -d postgres

```

---

## Run Migrations

```bash

uv run alembic upgrade head

```

---

## Start API

```bash

uv run uvicorn linguamentis.main:app --reload

```

API documentation is available through FastAPI's development documentation endpoints.

---

# Development Principles

### Keep the domain clean

Do not introduce framework dependencies into domain objects.

### Keep AI behind an abstraction

Agents should not know about OpenRouter.

### Keep state deterministic

The application controls the MindQuest state machine.

### Keep evaluation independent

Agents do not evaluate themselves.

### Preserve evidence

Scores without supporting evidence are insufficient.

### Prefer simplicity

LinguaMentis V1 intentionally avoids unnecessary infrastructure.

No:

- Kafka

- microservices

- event sourcing

- Redis

- Celery

- vector database

- complex recommendation engine

unless a concrete product requirement later justifies them.

---

# V1 Vertical Slice

The first complete backend slice should be:

```text

Create MindQuest
      ↓
Blue introduces topic
      ↓
Black Hat challenge
      ↓
Learner response
      ↓
Persist response
      ↓
Thinking Evaluation
      +
German Evaluation
      ↓
Evidence
      ↓
Feedback
      ↓
Next Black challenge
      ↓
Complete Black Hat

```

Once this works reliably, the remaining Hats can be added using the same architecture.

---

# Related Documents

From the repository root:

```text

PRD.md

HatContracts.md

EvaluationRubric.md

Architecture.md

README.md

```

These documents define the product, cognitive contracts, evaluation methodology, architecture, and project overview.

---

# Status

**V1 — Architecture and implementation in progress.**

The immediate priority is a reliable end-to-end vertical slice before expanding the system.

---

## Product Philosophy

> \*\*Language is the medium.

> Thinking is the skill.

> Perspective is the method.

> Growth is the outcome.\*\*
