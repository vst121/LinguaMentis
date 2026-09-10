# LinguaMentis — Architecture

**Version:** 1.0

**Status:** Draft

**Project:** LinguaMentis

**Primary Experience:** MindQuest

---

# 1. Architecture Overview

LinguaMentis is an AI-powered, gamified intellectual debate platform for B2/C1 German learners.

The V1 architecture follows a **modular monolith** approach:

- Python 3.12

- FastAPI

- PostgreSQL

- SQLAlchemy 2.x

- Alembic

- Next.js

- TypeScript

- React

- Tailwind CSS

- OpenRouter for LLM access

The architecture intentionally avoids unnecessary distributed infrastructure.

The central architectural principle is:

> **The application owns the MindQuest state. AI provides intelligence, not application control.**

---

# 2. Architectural Goals

The architecture should provide:

1\. Clear separation between domain logic and infrastructure.

2\. Explicit MindQuest state management.

3\. Independent Thinking and German evaluation.

4\. Strict behavioral boundaries for Six Thinking Hat agents.

5\. Structured AI outputs.

6\. Persistent learning history.

7\. Evidence-based evaluation.

8\. Replaceable LLM providers/models.

9\. Testable AI behavior.

10\. A foundation for a future evaluation harness.

11\. Simple V1 deployment and development.

12\. A clear path to future scaling without premature complexity.

---

# 3. High-Level Architecture

```text

                        LINGUAMENTIS
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
         Next.js Frontend          Python 3.12 Backend
                │                         │
                │                    FastAPI API
                │                         │
                │                  Application Layer
                │                         │
                │                  MindQuest Engine
                │                         │
                │             ┌───────────┴───────────┐
                │             │                       │
                │             ▼                       ▼
                │        Agent System           Evaluation
                │             │                  Pipeline
                │             │                 ┌─────┴─────┐
                │             │                 ▼           ▼
                │             │            Thinking      German
                │             │            Evaluator    Evaluator
                │             │                 │           │
                │             └─────────────────┴───────────┘
                │                               │
                │                               ▼
                │                         AI Gateway
                │                               │
                │                               ▼
                │                          OpenRouter
                │
                └────────────── HTTP API ────────────────┐
                                                         │
                                                         ▼
                                                     PostgreSQL

```

---

# 4. Architectural Style

LinguaMentis V1 uses a **modular monolith**.

The backend is deployed as one application, but its internal architecture is divided into explicit modules.

```text

API
│
▼
Application
│
▼
Domain
│
▼

Infrastructure

```

AI integration is isolated behind an AI Gateway:

```text

Agent
 │
 ▼
LLM Client
 │
 ▼
OpenRouter

```

The domain does not depend on OpenRouter.

---

# 5. Repository Structure

```text

linguamentis/
│
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── .env.example
│   │
│   ├── src/
│   │   └── linguamentis/
│   │       │
│   │       ├── main.py
│   │       │
│   │       ├── api/
│   │       │   ├── dependencies.py
│   │       │   ├── router.py
│   │       │   │
│   │       │   └── v1/
│   │       │       ├── mindquests.py
│   │       │       ├── turns.py
│   │       │       ├── evaluations.py
│   │       │       ├── users.py
│   │       │       └── learning.py
│   │       │
│   │       ├── application/
│   │       │   │
│   │       │   ├── mindquests/
│   │       │   │   ├── commands.py
│   │       │   │   ├── queries.py
│   │       │   │   └── service.py
│   │       │   │
│   │       │   ├── turns/
│   │       │   │   └── service.py
│   │       │   │
│   │       │   ├── evaluation/
│   │       │   │   └── service.py
│   │       │   │
│   │       │   └── learning/
│   │       │       └── service.py
│   │       │
│   │       ├── domain/
│   │       │   │
│   │       │   ├── users/
│   │       │   │   ├── entities.py
│   │       │   │   └── value\_objects.py
│   │       │   │
│   │       │   ├── mindquests/
│   │       │   │   ├── entities.py
│   │       │   │   ├── enums.py
│   │       │   │   ├── value\_objects.py
│   │       │   │   └── state\_machine.py
│   │       │   │
│   │       │   ├── hats/
│   │       │   │   ├── contracts.py
│   │       │   │   ├── definitions.py
│   │       │   │   └── types.py
│   │       │   │
│   │       │   ├── evaluations/
│   │       │   │   ├── thinking.py
│   │       │   │   ├── german.py
│   │       │   │   └── evidence.py
│   │       │   │
│   │       │   └── learning/
│   │       │       └── profile.py
│   │       │
│   │       ├── agents/
│   │       │   ├── base.py
│   │       │   ├── registry.py
│   │       │   ├── blue.py
│   │       │   ├── white.py
│   │       │   ├── red.py
│   │       │   ├── black.py
│   │       │   ├── yellow.py
│   │       │   └── green.py
│   │       │
│   │       ├── ai/
│   │       │   ├── client.py
│   │       │   ├── models.py
│   │       │   ├── prompts.py
│   │       │   ├── gateway.py
│   │       │   └── openrouter.py
│   │       │
│   │       ├── infrastructure/
│   │       │   ├── database/
│   │       │   │   ├── session.py
│   │       │   │   ├── models.py
│   │       │   │   └── repositories/
│   │       │   │
│   │       │   └── configuration.py
│   │       │
│   │       └── shared/
│   │           ├── exceptions.py
│   │           ├── logging.py
│   │           └── result.py
│   │
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── evaluation/
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   │
│   └── src/
│       ├── app/
│       │   ├── page.tsx
│       │   ├── mindquests/
│       │   │   ├── page.tsx
│       │   │   └── \[id]/
│       │   │       ├── page.tsx
│       │   │       └── reflection/
│       │   │           └── page.tsx
│       │   ├── learning/
│       │   │   └── page.tsx
│       │   └── history/
│       │       └── page.tsx
│       │
│       ├── components/
│       │   ├── mindquest/
│       │   ├── hats/
│       │   ├── evaluation/
│       │   ├── reflection/
│       │   └── ui/
│       │
│       ├── services/
│       │   └── api/
│       │
│       ├── types/
│       │
│       └── lib/
│
├── docs/
│   ├── PRD.md
│   ├── Architecture.md
│   ├── HatContracts.md
│   ├── EvaluationRubric.md
│   └── AIContracts.md
│
├── docker-compose.yml
└── README.md

```

---

# 6. Backend Architecture

The backend consists of five major areas:

```text

API

Application

Domain

Agents

Infrastructure

```

AI is isolated as a dedicated capability:

```text

AI Gateway

```

---

# 7. API Layer

The API layer is responsible only for HTTP concerns.

Responsibilities:

- HTTP routing

- Request validation

- Response serialization

- Dependency injection

- HTTP error handling

- API versioning

The API layer must not contain business rules.

Example:

```text

POST /api/v1/mindquests/{id}/responses

```

The endpoint delegates to the application layer:

```text

FastAPI Endpoint
     ↓
MindQuestService
     ↓
MindQuestEngine

```

---

# 8. Application Layer

The application layer coordinates use cases.

Primary application services:

```text

MindQuestService

TurnService

EvaluationService

LearningService

```

The application layer coordinates domain objects, agents, evaluators, and repositories.

Example:

```text

Submit Response
     │
     ▼
MindQuestService
     │
     ▼
MindQuestEngine
     │
     ├── Validate state
     │
     ├── Persist response
     │
     ├── Evaluate thinking
     │
     ├── Evaluate German
     │
     ├── Generate feedback
     │
     ├── Determine next challenge
     │
     └── Persist result

```

---

# 9. Domain Layer

The domain layer contains the core business concepts of LinguaMentis.

It must not depend on:

- FastAPI

- PostgreSQL

- SQLAlchemy

- OpenRouter

- HTTP

- Next.js

- specific LLM providers

Core domain concepts:

```text

User

MindQuest

HatRound

Turn

ThinkingEvaluation

GermanEvaluation

Evidence

FinalReflection

UserActivity

UserLearningProfile

```

---

# 10. MindQuest Domain

A MindQuest represents one complete intellectual exploration.

Conceptually:

```python

class MindQuest:

   id: UUID

   user\_id: UUID

   topic: str

   target\_level: LanguageLevel

   status: MindQuestStatus

   current\_hat: HatType | None

```

The MindQuest domain is responsible for enforcing valid lifecycle transitions.

---

# 11. MindQuest State Machine

The application uses an explicit state machine.

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
HAT\_ACTIVE
  ↓

...

  ↓
ALL\_HATS\_COMPLETED
  ↓
FINAL\_EVALUATION
  ↓
COMPLETED

```

The state machine is deterministic and application-controlled.

The LLM cannot directly change the state.

---

# 12. MindQuest Engine

The `MindQuestEngine` coordinates the complete MindQuest lifecycle.

Conceptual interface:

```python

class MindQuestEngine:



   async def start(

       self,

       mindquest\_id: UUID,

   ) -> MindQuestResult:

       ...



   async def submit\_response(

       self,

       mindquest\_id: UUID,

       response: str,

   ) -> TurnResult:

       ...



   async def advance(

       self,

       mindquest\_id: UUID,

   ) -> MindQuestResult:

       ...



   async def complete(

       self,

       mindquest\_id: UUID,

   ) -> FinalReflection:

       ...

```

The engine is the main orchestration boundary between application state and AI capabilities.

---

# 13. Six Thinking Hat Agents

The agent architecture is:

```text

HatAgent
   │
   ├── WhiteHatAgent
   ├── RedHatAgent
   ├── BlackHatAgent
   ├── YellowHatAgent
   ├── GreenHatAgent
   └── BlueHatAgent

```

Each agent has a specific responsibility.

Agents do not directly modify domain state.

---

# 14. Hat Agent Interface

Conceptual interface:

```python

class HatAgent(ABC):



   @property

   @abstractmethod

   def hat(self) -> HatType:

       ...



   @abstractmethod

   async def create\_challenge(

       self,

       context: MindQuestContext,

   ) -> HatChallenge:

       ...

```

The agent receives controlled context.

It should not receive unrestricted database access.

---

# 15. Agent Registry

Agents are resolved through an `AgentRegistry`.

```text

AgentRegistry
     │
     ├── WHITE  → WhiteHatAgent
     ├── RED    → RedHatAgent
     ├── BLACK  → BlackHatAgent
     ├── YELLOW → YellowHatAgent
     ├── GREEN  → GreenHatAgent
     └── BLUE   → BlueHatAgent

```

Conceptually:

```python

agent = registry.get(HatType.BLACK)



challenge = await agent.create\_challenge(context)

```

This avoids coupling the Blue Agent to concrete agent implementations.

---

# 16. Hat Contracts

Each hat has an explicit contract.

```python

@dataclass(frozen=True)

class HatContract:

   hat: HatType

   goal: str

   should: tuple\[str, ...]

   should\_not: tuple\[str, ...]

   dimensions: tuple\[str, ...]

```

Example:

```python

BLACK\_HAT\_CONTRACT = HatContract(

   hat=HatType.BLACK,

   goal="Identify risks, weaknesses and negative consequences.",

   should=(

       "Challenge assumptions",

       "Identify potential problems",

       "Explore consequences",

       "Demand specificity",

   ),

   should\_not=(

       "Propose solutions",

       "Focus on benefits",

       "Express emotions",

   ),

   dimensions=(

       "risk\_identification",

       "causal\_reasoning",

       "consequence\_analysis",

       "specificity",

       "hat\_adherence",

   ),

)

```

Contracts are used by both the agent and the evaluation system.

---

# 17. Blue Agent

The Blue Agent is the process orchestrator.

Responsibilities:

- Start MindQuest

- Introduce topic

- Select/manage hats

- Explain challenges

- Track progress

- Coordinate Hat Agents

- Decide when a phase is sufficiently explored

- Transition between hats

- Detect completion

- Trigger final reflection

The Blue Agent must not become the user's primary thinking agent.

---

# 18. Evaluation Architecture

Thinking and German evaluation are independent.

```text

                    User Response
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    Thinking Evaluator           German Evaluator
            │                           │
            ▼                           ▼
  ThinkingEvaluation            GermanEvaluation
            │                           │
            └─────────────┬─────────────┘
                          ▼
                        Evidence
                          │
                          ▼
                       Feedback

```

The system must never replace these with one combined score.

---

# 19. Thinking Evaluator

The Thinking Evaluator evaluates intellectual performance.

Dimensions depend on the active hat.

Possible dimensions:

- Hat adherence

- Relevance

- Depth

- Reasoning

- Specificity

- Causal reasoning

- Consequence analysis

- Creativity

- Perspective awareness

For Black Hat:

```text

Risk identification

Causal reasoning

Consequence analysis

Specificity

Hat adherence

```

---

# 20. German Evaluator

The German Evaluator independently evaluates language quality.

Dimensions:

```text

Grammar

Vocabulary

Sentence structure

Naturalness

Fluency

Level appropriateness

Precision

```

The evaluator should distinguish:

```text

Incorrect

Correct but unnatural

Acceptable but simple

Advanced and natural

```

---

# 21. Evidence

Evidence is a first-class domain concept.

An evaluation should not only contain:

```text

Score = 78

```

It should explain why.

Thinking evidence:

```text

- Identified a genuine risk

- Explained a consequence

- Stayed within Black Hat

- Challenged an assumption

```

German evidence:

```text

- Correct conditional construction

- Appropriate B2 vocabulary

- Incorrect word order

- Unnatural expression

```

Evidence is persisted and contributes to the user's learning history.

---

# 22. AI Gateway

All LLM communication goes through an abstraction.

```text

Agent
  ↓
ILLMClient
  ↓
OpenRouterClient
  ↓
OpenRouter API

```

Agents must never directly depend on OpenRouter.

Conceptual interface:

```python

class LLMClient(Protocol):



   async def generate\_structured(

       self,

       *,

       system\_prompt: str,

       user\_prompt: str,

       response\_model: type\[T],

       model: str,

   ) -> T:

       ...

```

Implementation:

```text

OpenRouterClient

```

This allows another provider to be introduced later without changing domain or agent logic.

---

# 23. OpenRouter Model Configuration

Models should be configurable.

Example environment variables:

```text

AI\_MODEL\_BLUE

AI\_MODEL\_HAT

AI\_MODEL\_THINKING\_EVALUATOR

AI\_MODEL\_GERMAN\_EVALUATOR

AI\_MODEL\_REFLECTION

```

The application should never assume that a particular model is permanently responsible for a task.

This makes model experimentation and evaluation possible.

---

# 24. Structured AI Outputs

Important AI interactions must use structured outputs.

Primary AI contracts:

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

Thinking:

```python

class ThinkingEvaluation(BaseModel):

   score: int

   hat\_adherence: int

   reasoning: int

   depth: int

   specificity: int



   evidence: list\[Evidence]

   strengths: list\[str]

   weaknesses: list\[str]

   recommendations: list\[str]

```

German:

```python

class GermanEvaluation(BaseModel):

   score: int

   grammar: int

   vocabulary: int

   sentence\_structure: int

   naturalness: int

   level\_appropriateness: int



   evidence: list\[Evidence]

   corrections: list\[Correction]

   strengths: list\[str]

   weaknesses: list\[str]

   recommendations: list\[str]

```

---

# 25. AI Context

Agents should receive a controlled `MindQuestContext`.

The context may contain:

```text

MindQuest ID

Topic

Target language level

Current hat

Current turn

Relevant previous responses

Previous feedback

Current progress

```

Agents should not receive unrestricted access to:

```text

Database

Repositories

Application services

Infrastructure

```

This keeps agent behavior bounded.

---

# 26. Persistence Architecture

PostgreSQL is the V1 persistence layer.

Initial tables:

```text

users

mind\_quests

hat\_rounds

turns

thinking\_evaluations

german\_evaluations

evidence

user\_activities

final\_reflections

```

Relationships:

```text

User
│
├── MindQuest
│      │
│      ├── HatRound
│      │      │
│      │      └── Turn
│      │             ├── Response
│      │             ├── ThinkingEvaluation
│      │             └── GermanEvaluation
│      │                    └── Evidence
│      │
│      └── FinalReflection
│
└── UserActivity

```

---

# 27. Database Technology

Recommended:

- PostgreSQL

- SQLAlchemy 2.x

- Alembic

- Async database access

The domain model should remain independent from SQLAlchemy models where practical.

Repository interfaces belong to the application/domain boundary.

SQLAlchemy implementations belong to infrastructure.

---

# 28. User

A `User` entity exists in V1.

Authentication is explicitly out of scope.

V1 assumes one predefined user.

All user-owned data must reference:

```text

UserId

```

This provides a clean path toward multiple users later without redesigning the domain.

---

# 29. User Learning Profile

The learning profile is derived from the user's accumulated journey.

```text

MindQuest History
      ↓
Evaluations
      ↓
Evidence
      ↓
Learning Profile Service
      ↓
UserLearningProfile

```

Possible dimensions:

```text

Thinking
├── Critical Thinking
├── Creativity
├── Reasoning
├── Perspective Shifting
└── Depth



German
├── Grammar
├── Vocabulary
├── Naturalness
├── Sentence Structure
└── Advanced Expression

```

The profile should not be manually maintained as the source of truth.

---

# 30. User Activity

Activities provide a chronological view of the learning journey.

Possible types:

```text

MindQuestStarted

TopicSelected

HatSelected

ResponseSubmitted

ThinkingEvaluated

GermanEvaluated

HatCompleted

AchievementUnlocked

MindQuestCompleted

```

`UserActivity` is not the authoritative source of domain state.

The domain entities remain authoritative.

---

# 31. Complete Learning Journey

The system must preserve historical learning data.

It should not store only the latest score.

Example:

```text

MindQuest 1
├── Responses
├── Thinking Evaluations
├── German Evaluations
└── Reflection


MindQuest 2
├── Responses
├── Thinking Evaluations
├── German Evaluations
└── Reflection


MindQuest 3
└── ...

         ↓

Derived Learning Profile

```

This enables progress analysis over time.

---

# 32. API Design

The initial API should remain small.

## MindQuest

```http

POST   /api/v1/mindquests

GET    /api/v1/mindquests

GET    /api/v1/mindquests/{id}

POST   /api/v1/mindquests/{id}/start

POST   /api/v1/mindquests/{id}/responses

POST   /api/v1/mindquests/{id}/advance

GET    /api/v1/mindquests/{id}/reflection

```

## Learning

```http

GET /api/v1/users/{user\_id}/learning-profile

GET /api/v1/users/{user\_id}/activities

GET /api/v1/users/{user\_id}/mindquests

```

The API should expose use cases rather than internal implementation details.

---

# 33. Response Processing Flow

When the user submits a response:

```text

POST /mindquests/{id}/responses
               │
               ▼
       MindQuestService
               │
               ▼
        Validate State
               │
               ▼
       Persist User Response
               │
       ┌───────┴────────┐
       ▼                ▼
Thinking Evaluator   German Evaluator
       │                │
       └───────┬────────┘
               ▼
            Evidence
               │
               ▼
            Feedback
               │
               ▼
       Next Challenge
               │
               ▼
       Persist MindQuest
               │
               ▼
         API Response

```

---

# 34. Parallel Evaluation

Thinking and German evaluation are independent.

Python async execution should therefore allow parallel evaluation.

Conceptually:

```python

thinking\_task = evaluate\_thinking(...)

german\_task = evaluate\_german(...)



thinking, german = await asyncio.gather(

   thinking\_task,

   german\_task,

)

```

This reduces overall response latency compared with sequential evaluation.

---

# 35. Failure Handling

AI failures must not corrupt the MindQuest.

Example:

```text

User Response
     ↓
Persist Response
     ↓
OpenRouter Failure

```

The response should remain persisted.

The system should distinguish:

```text

Response persisted

Evaluation pending

Evaluation failed

Evaluation completed

```

The LLM is therefore not required for maintaining core application consistency.

---

# 36. Frontend Architecture

The frontend uses:

- Next.js

- TypeScript

- React

- Tailwind CSS

Suggested structure:

```text

frontend/src/
├── app/
│
├── components/
│   ├── mindquest/
│   ├── hats/
│   ├── evaluation/
│   ├── reflection/
│   └── ui/
│
├── services/
│   └── api/
│
├── types/
│
└── lib/

```

---

# 37. MindQuest UI Components

```text

components/
│
├── mindquest/
│   ├── MindQuestHeader
│   ├── MindQuestProgress
│   ├── ChallengeCard
│   ├── ResponseEditor
│   └── MindQuestTimeline
│
├── hats/
│   ├── HatIndicator
│   ├── HatProgress
│   └── HatChallenge
│
├── evaluation/
│   ├── ThinkingEvaluation
│   ├── GermanEvaluation
│   ├── EvidenceList
│   ├── CorrectionList
│   └── RecommendationList
│
└── reflection/
   ├── ThinkingReflection
   ├── GermanReflection
   └── ProgressComparison

```

The frontend structure mirrors the product domain.

---

# 38. Frontend State

The backend remains authoritative for MindQuest state.

Backend owns:

```text

Current hat

Current turn

Scores

Evaluations

MindQuest status

Progress

```

Frontend owns temporary UI state:

```text

Response draft

Dialogs

Animations

UI preferences

Temporary interaction state

```

This prevents client/server state divergence.

---

# 39. V1 Interaction Model

The initial interaction is synchronous from the user's perspective.

```text

User writes response
       ↓
Submit
       ↓
Thinking evaluation
\+
German evaluation
       ↓
Feedback
       ↓
Next challenge

```

The system may internally perform multiple asynchronous operations, but the user experiences one coherent turn.

---

# 40. Docker Architecture

Development environment:

```text

Docker Compose
│
├── frontend
│
├── backend
│
└── postgres

```

OpenRouter remains an external API:

```text

Backend
  │
  ▼
OpenRouter

```

No local LLM infrastructure is required for V1.

---

# 41. Configuration

Configuration is environment-based.

Example:

```text

DATABASE\_URL



OPENROUTER\_API\_KEY

OPENROUTER\_BASE\_URL



AI\_MODEL\_BLUE

AI\_MODEL\_HAT

AI\_MODEL\_THINKING\_EVALUATOR

AI\_MODEL\_GERMAN\_EVALUATOR

AI\_MODEL\_REFLECTION



ENVIRONMENT

LOG\_LEVEL

```

Use Pydantic Settings for backend configuration.

The OpenRouter API key must remain server-side and must never be exposed to Next.js.

---

# 42. Testing Architecture

Testing is divided into three levels.

```text

tests/

├── unit/
├── integration/
└── evaluation/

```

## Unit Tests

Test:

- Domain rules

- State transitions

- Hat Contracts

- Evaluation calculations

- Learning profile calculations

No real LLM calls.

## Integration Tests

Test:

- FastAPI

- PostgreSQL

- Repositories

- MindQuest workflows

- AI gateway integration using mocks where appropriate

## Evaluation Tests

Test real AI behavior against controlled datasets.

---

# 43. Evaluation Harness

The evaluation harness is a major future capability of LinguaMentis.

Suggested structure:

```text

evaluation/
│
├── datasets/
│   ├── thinking/
│   └── german/
│
├── cases/
├── runners/
├── metrics/
└── reports/

```

Each test case can contain:

```text

User Response

Active Hat

Target Level

Expected Thinking Behavior

Expected German Issues

Expected Evidence

```

The harness can measure:

### Thinking

- Hat adherence accuracy

- Evaluation consistency

- Score stability

- False positives

- False negatives

### German

- Correction accuracy

- Grammar detection

- Naturalness detection

- Vocabulary assessment

- Score consistency

### System

- Latency

- Cost

- Model performance

- Prompt regression

---

# 44. Model and Prompt Regression

The architecture should make it possible to compare:

```text

Model A + Prompt V1

       vs

Model A + Prompt V2

```

or:

```text

Model A

  vs

Model B

```

against the same evaluation dataset.

This makes the AI system measurable rather than relying only on subjective impressions.

---

# 45. Security Boundaries

Even though authentication is out of scope for V1, important boundaries should exist.

OpenRouter credentials:

```text

Browser

  X

OpenRouter API Key



Backend

  ↓

OpenRouter

```

The browser must never receive the OpenRouter API key.

AI prompts should also be treated as server-side implementation details.

---

# 46. Observability

V1 should have basic structured logging.

Useful fields:

```text

request\_id

mindquest\_id

user\_id

turn\_id

hat

model

operation

latency

evaluation\_type

```

Avoid logging sensitive or unnecessary user content.

AI calls should provide enough metadata to investigate:

- failures

- latency

- model behavior

- token/cost trends

---

# 47. Architectural Principles

LinguaMentis follows these principles:

### Principle 1 — Application owns state

The LLM never owns authoritative application state.

### Principle 2 — Agents are bounded

Each agent has a clear Hat Contract.

### Principle 3 — Agents are not evaluators

The agent that challenges the user should not judge its own performance.

### Principle 4 — Thinking and German are independent

They have separate scores, rubrics, evidence, and evaluation pipelines.

### Principle 5 — Structured AI

Important AI interactions use typed structured outputs.

### Principle 6 — Provider independence

Agents depend on `LLMClient`, not OpenRouter.

### Principle 7 — Evidence over scores

Evaluation must explain why a score was given.

### Principle 8 — Domain first

Business rules belong in the domain/application layers.

### Principle 9 — Preserve the journey

Historical MindQuests and evaluations are retained.

### Principle 10 — Simplicity first

Do not introduce distributed infrastructure until the product requires it.

---

# 48. Explicitly Out of Scope for V1

The following are intentionally excluded:

```text

Microservices

Kafka

Redis

Celery

Kubernetes

Event sourcing

Vector database

Authentication

Complex recommendation engine

Mobile application

Payments

Subscription management

Real-time voice

Advanced pronunciation analysis

Separate AI microservice

Separate evaluation microservice

```

These may become appropriate later, but they are not architectural requirements for the initial product.

---

# 49. Future Evolution

The architecture allows future evolution without changing the core domain.

Possible future additions:

```text

               LinguaMentis V1
                      │
            ┌─────────┴─────────┐
            ▼                   ▼
       Voice Layer        Advanced Analytics
            │                   │
            ▼                   ▼
         STT/TTS          Learning Insights
            │
            ▼
    Speaking Evaluation

```

If scale eventually requires it, individual capabilities can later be extracted from the modular monolith.

The initial architecture should not assume that extraction is necessary.

---

# 50. First Vertical Slice

The first implementation should focus on one complete Black Hat experience.

```text

Blue Agent
     ↓
Select Topic
     ↓
Black Hat Agent
     ↓
Generate Challenge
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
Repeat
     ↓
Blue Final Reflection

```

This validates the most important architectural boundaries before implementing all six hats.

---

# 51. Recommended Implementation Order

```text

1\. Project setup
      ↓
2\. PostgreSQL + SQLAlchemy + Alembic
      ↓
3\. Domain entities
      ↓
4\. MindQuest state machine
      ↓
5\. Hat Contracts
      ↓
6\. AI/Pydantic contracts
      ↓
7\. LLM Gateway
      ↓
8\. OpenRouter integration
      ↓
9\. BlackHatAgent
      ↓
10\. ThinkingEvaluator
      ↓
11\. GermanEvaluator
      ↓
12\. Evidence persistence
      ↓
13\. MindQuest Engine
      ↓
14\. FastAPI endpoints
      ↓
15\. Next.js MindQuest UI
      ↓
16\. Complete Black Hat vertical slice
      ↓
17\. Remaining five hats
      ↓
18\. Blue orchestration
      ↓
19\. Gamification
      ↓
20\. Evaluation Harness
      ↓
21\. Voice

```

---

# 52. Final Architecture Statement

LinguaMentis is a **modular monolith with an AI-native domain architecture**.

Its core architecture can be summarized as:

```text

Next.js

  │
  ▼
FastAPI
  │
  ▼
Application Layer
  │
  ├───────────────┐
  ▼               ▼
MindQuest       Evaluation
Engine          Pipeline
  │               │
  ▼               ├── Thinking Evaluator
Agents            └── German Evaluator
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

The most important architectural rule is:

> **LinguaMentis is an AI-enabled application, not an LLM-controlled application.**

The application owns:

```text

MindQuest state

Lifecycle

Turns

Persistence

Scores

Learning history

```

AI provides:

```text

Challenges

Questions

Evaluations

Evidence

Feedback

Recommendations

Reflection

```

This separation gives LinguaMentis a strong foundation for production-quality development while keeping V1 intentionally simple.
