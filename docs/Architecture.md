\# LinguaMentis — Architecture



\*\*Version:\*\* 1.0

\*\*Status:\*\* Draft

\*\*Project:\*\* LinguaMentis

\*\*Primary Experience:\*\* MindQuest



\---



\# 1. Architecture Overview



LinguaMentis is an AI-powered, gamified intellectual debate platform for B2/C1 German learners.



The V1 architecture follows a \*\*modular monolith\*\* approach:



\* Python 3.12

\* FastAPI

\* PostgreSQL

\* SQLAlchemy 2.x

\* Alembic

\* Next.js

\* TypeScript

\* React

\* Tailwind CSS

\* OpenRouter for LLM access



The architecture intentionally avoids unnecessary distributed infrastructure.



The central architectural principle is:



> \*\*The application owns the MindQuest state. AI provides intelligence, not application control.\*\*



\---



\# 2. Architectural Goals



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



\---



\# 3. High-Level Architecture



```text

&#x20;                        LINGUAMENTIS

&#x20;                             │

&#x20;                ┌────────────┴────────────┐

&#x20;                │                         │

&#x20;                ▼                         ▼

&#x20;         Next.js Frontend          Python 3.12 Backend

&#x20;                │                         │

&#x20;                │                    FastAPI API

&#x20;                │                         │

&#x20;                │                  Application Layer

&#x20;                │                         │

&#x20;                │                  MindQuest Engine

&#x20;                │                         │

&#x20;                │             ┌───────────┴───────────┐

&#x20;                │             │                       │

&#x20;                │             ▼                       ▼

&#x20;                │        Agent System           Evaluation

&#x20;                │             │                  Pipeline

&#x20;                │             │                 ┌─────┴─────┐

&#x20;                │             │                 ▼           ▼

&#x20;                │             │            Thinking      German

&#x20;                │             │            Evaluator    Evaluator

&#x20;                │             │                 │           │

&#x20;                │             └─────────────────┴───────────┘

&#x20;                │                               │

&#x20;                │                               ▼

&#x20;                │                         AI Gateway

&#x20;                │                               │

&#x20;                │                               ▼

&#x20;                │                          OpenRouter

&#x20;                │

&#x20;                └────────────── HTTP API ────────────────┐

&#x20;                                                           │

&#x20;                                                           ▼

&#x20;                                                      PostgreSQL

```



\---



\# 4. Architectural Style



LinguaMentis V1 uses a \*\*modular monolith\*\*.



The backend is deployed as one application, but its internal architecture is divided into explicit modules.



```text

API

&#x20;│

&#x20;▼

Application

&#x20;│

&#x20;▼

Domain

&#x20;│

&#x20;▼

Infrastructure

```



AI integration is isolated behind an AI Gateway:



```text

Agent

&#x20; │

&#x20; ▼

LLM Client

&#x20; │

&#x20; ▼

OpenRouter

```



The domain does not depend on OpenRouter.



\---



\# 5. Repository Structure



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



\---



\# 6. Backend Architecture



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



\---



\# 7. API Layer



The API layer is responsible only for HTTP concerns.



Responsibilities:



\* HTTP routing

\* Request validation

\* Response serialization

\* Dependency injection

\* HTTP error handling

\* API versioning



The API layer must not contain business rules.



Example:



```text

POST /api/v1/mindquests/{id}/responses

```



The endpoint delegates to the application layer:



```text

FastAPI Endpoint

&#x20;     ↓

MindQuestService

&#x20;     ↓

MindQuestEngine

```



\---



\# 8. Application Layer



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

&#x20;     │

&#x20;     ▼

MindQuestService

&#x20;     │

&#x20;     ▼

MindQuestEngine

&#x20;     │

&#x20;     ├── Validate state

&#x20;     │

&#x20;     ├── Persist response

&#x20;     │

&#x20;     ├── Evaluate thinking

&#x20;     │

&#x20;     ├── Evaluate German

&#x20;     │

&#x20;     ├── Generate feedback

&#x20;     │

&#x20;     ├── Determine next challenge

&#x20;     │

&#x20;     └── Persist result

```



\---



\# 9. Domain Layer



The domain layer contains the core business concepts of LinguaMentis.



It must not depend on:



\* FastAPI

\* PostgreSQL

\* SQLAlchemy

\* OpenRouter

\* HTTP

\* Next.js

\* specific LLM providers



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



\---



\# 10. MindQuest Domain



A MindQuest represents one complete intellectual exploration.



Conceptually:



```python

class MindQuest:

&#x20;   id: UUID

&#x20;   user\_id: UUID

&#x20;   topic: str

&#x20;   target\_level: LanguageLevel

&#x20;   status: MindQuestStatus

&#x20;   current\_hat: HatType | None

```



The MindQuest domain is responsible for enforcing valid lifecycle transitions.



\---



\# 11. MindQuest State Machine



The application uses an explicit state machine.



```text

CREATED

&#x20;  ↓

TOPIC\_SELECTED

&#x20;  ↓

IN\_PROGRESS

&#x20;  ↓

HAT\_ACTIVE

&#x20;  ↓

HAT\_COMPLETED

&#x20;  ↓

HAT\_ACTIVE

&#x20;  ↓

...

&#x20;  ↓

ALL\_HATS\_COMPLETED

&#x20;  ↓

FINAL\_EVALUATION

&#x20;  ↓

COMPLETED

```



The state machine is deterministic and application-controlled.



The LLM cannot directly change the state.



\---



\# 12. MindQuest Engine



The `MindQuestEngine` coordinates the complete MindQuest lifecycle.



Conceptual interface:



```python

class MindQuestEngine:



&#x20;   async def start(

&#x20;       self,

&#x20;       mindquest\_id: UUID,

&#x20;   ) -> MindQuestResult:

&#x20;       ...



&#x20;   async def submit\_response(

&#x20;       self,

&#x20;       mindquest\_id: UUID,

&#x20;       response: str,

&#x20;   ) -> TurnResult:

&#x20;       ...



&#x20;   async def advance(

&#x20;       self,

&#x20;       mindquest\_id: UUID,

&#x20;   ) -> MindQuestResult:

&#x20;       ...



&#x20;   async def complete(

&#x20;       self,

&#x20;       mindquest\_id: UUID,

&#x20;   ) -> FinalReflection:

&#x20;       ...

```



The engine is the main orchestration boundary between application state and AI capabilities.



\---



\# 13. Six Thinking Hat Agents



The agent architecture is:



```text

HatAgent

&#x20;   │

&#x20;   ├── WhiteHatAgent

&#x20;   ├── RedHatAgent

&#x20;   ├── BlackHatAgent

&#x20;   ├── YellowHatAgent

&#x20;   ├── GreenHatAgent

&#x20;   └── BlueHatAgent

```



Each agent has a specific responsibility.



Agents do not directly modify domain state.



\---



\# 14. Hat Agent Interface



Conceptual interface:



```python

class HatAgent(ABC):



&#x20;   @property

&#x20;   @abstractmethod

&#x20;   def hat(self) -> HatType:

&#x20;       ...



&#x20;   @abstractmethod

&#x20;   async def create\_challenge(

&#x20;       self,

&#x20;       context: MindQuestContext,

&#x20;   ) -> HatChallenge:

&#x20;       ...

```



The agent receives controlled context.



It should not receive unrestricted database access.



\---



\# 15. Agent Registry



Agents are resolved through an `AgentRegistry`.



```text

AgentRegistry

&#x20;     │

&#x20;     ├── WHITE  → WhiteHatAgent

&#x20;     ├── RED    → RedHatAgent

&#x20;     ├── BLACK  → BlackHatAgent

&#x20;     ├── YELLOW → YellowHatAgent

&#x20;     ├── GREEN  → GreenHatAgent

&#x20;     └── BLUE   → BlueHatAgent

```



Conceptually:



```python

agent = registry.get(HatType.BLACK)



challenge = await agent.create\_challenge(context)

```



This avoids coupling the Blue Agent to concrete agent implementations.



\---



\# 16. Hat Contracts



Each hat has an explicit contract.



```python

@dataclass(frozen=True)

class HatContract:

&#x20;   hat: HatType

&#x20;   goal: str

&#x20;   should: tuple\[str, ...]

&#x20;   should\_not: tuple\[str, ...]

&#x20;   dimensions: tuple\[str, ...]

```



Example:



```python

BLACK\_HAT\_CONTRACT = HatContract(

&#x20;   hat=HatType.BLACK,

&#x20;   goal="Identify risks, weaknesses and negative consequences.",

&#x20;   should=(

&#x20;       "Challenge assumptions",

&#x20;       "Identify potential problems",

&#x20;       "Explore consequences",

&#x20;       "Demand specificity",

&#x20;   ),

&#x20;   should\_not=(

&#x20;       "Propose solutions",

&#x20;       "Focus on benefits",

&#x20;       "Express emotions",

&#x20;   ),

&#x20;   dimensions=(

&#x20;       "risk\_identification",

&#x20;       "causal\_reasoning",

&#x20;       "consequence\_analysis",

&#x20;       "specificity",

&#x20;       "hat\_adherence",

&#x20;   ),

)

```



Contracts are used by both the agent and the evaluation system.



\---



\# 17. Blue Agent



The Blue Agent is the process orchestrator.



Responsibilities:



\* Start MindQuest

\* Introduce topic

\* Select/manage hats

\* Explain challenges

\* Track progress

\* Coordinate Hat Agents

\* Decide when a phase is sufficiently explored

\* Transition between hats

\* Detect completion

\* Trigger final reflection



The Blue Agent must not become the user's primary thinking agent.



\---



\# 18. Evaluation Architecture



Thinking and German evaluation are independent.



```text

&#x20;                    User Response

&#x20;                          │

&#x20;            ┌─────────────┴─────────────┐

&#x20;            ▼                           ▼

&#x20;    Thinking Evaluator           German Evaluator

&#x20;            │                           │

&#x20;            ▼                           ▼

&#x20;  ThinkingEvaluation            GermanEvaluation

&#x20;            │                           │

&#x20;            └─────────────┬─────────────┘

&#x20;                          ▼

&#x20;                        Evidence

&#x20;                          │

&#x20;                          ▼

&#x20;                       Feedback

```



The system must never replace these with one combined score.



\---



\# 19. Thinking Evaluator



The Thinking Evaluator evaluates intellectual performance.



Dimensions depend on the active hat.



Possible dimensions:



\* Hat adherence

\* Relevance

\* Depth

\* Reasoning

\* Specificity

\* Causal reasoning

\* Consequence analysis

\* Creativity

\* Perspective awareness



For Black Hat:



```text

Risk identification

Causal reasoning

Consequence analysis

Specificity

Hat adherence

```



\---



\# 20. German Evaluator



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



\---



\# 21. Evidence



Evidence is a first-class domain concept.



An evaluation should not only contain:



```text

Score = 78

```



It should explain why.



Thinking evidence:



```text

\- Identified a genuine risk

\- Explained a consequence

\- Stayed within Black Hat

\- Challenged an assumption

```



German evidence:



```text

\- Correct conditional construction

\- Appropriate B2 vocabulary

\- Incorrect word order

\- Unnatural expression

```



Evidence is persisted and contributes to the user's learning history.



\---



\# 22. AI Gateway



All LLM communication goes through an abstraction.



```text

Agent

&#x20;  ↓

ILLMClient

&#x20;  ↓

OpenRouterClient

&#x20;  ↓

OpenRouter API

```



Agents must never directly depend on OpenRouter.



Conceptual interface:



```python

class LLMClient(Protocol):



&#x20;   async def generate\_structured(

&#x20;       self,

&#x20;       \*,

&#x20;       system\_prompt: str,

&#x20;       user\_prompt: str,

&#x20;       response\_model: type\[T],

&#x20;       model: str,

&#x20;   ) -> T:

&#x20;       ...

```



Implementation:



```text

OpenRouterClient

```



This allows another provider to be introduced later without changing domain or agent logic.



\---



\# 23. OpenRouter Model Configuration



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



\---



\# 24. Structured AI Outputs



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

&#x20;   question: str

&#x20;   instruction: str

&#x20;   expected\_thinking\_mode: HatType

&#x20;   difficulty: int

```



Thinking:



```python

class ThinkingEvaluation(BaseModel):

&#x20;   score: int

&#x20;   hat\_adherence: int

&#x20;   reasoning: int

&#x20;   depth: int

&#x20;   specificity: int



&#x20;   evidence: list\[Evidence]

&#x20;   strengths: list\[str]

&#x20;   weaknesses: list\[str]

&#x20;   recommendations: list\[str]

```



German:



```python

class GermanEvaluation(BaseModel):

&#x20;   score: int

&#x20;   grammar: int

&#x20;   vocabulary: int

&#x20;   sentence\_structure: int

&#x20;   naturalness: int

&#x20;   level\_appropriateness: int



&#x20;   evidence: list\[Evidence]

&#x20;   corrections: list\[Correction]

&#x20;   strengths: list\[str]

&#x20;   weaknesses: list\[str]

&#x20;   recommendations: list\[str]

```



\---



\# 25. AI Context



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



\---



\# 26. Persistence Architecture



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

&#x20;│

&#x20;├── MindQuest

&#x20;│      │

&#x20;│      ├── HatRound

&#x20;│      │      │

&#x20;│      │      └── Turn

&#x20;│      │             ├── Response

&#x20;│      │             ├── ThinkingEvaluation

&#x20;│      │             └── GermanEvaluation

&#x20;│      │                    └── Evidence

&#x20;│      │

&#x20;│      └── FinalReflection

&#x20;│

&#x20;└── UserActivity

```



\---



\# 27. Database Technology



Recommended:



\* PostgreSQL

\* SQLAlchemy 2.x

\* Alembic

\* Async database access



The domain model should remain independent from SQLAlchemy models where practical.



Repository interfaces belong to the application/domain boundary.



SQLAlchemy implementations belong to infrastructure.



\---



\# 28. User



A `User` entity exists in V1.



Authentication is explicitly out of scope.



V1 assumes one predefined user.



All user-owned data must reference:



```text

UserId

```



This provides a clean path toward multiple users later without redesigning the domain.



\---



\# 29. User Learning Profile



The learning profile is derived from the user's accumulated journey.



```text

MindQuest History

&#x20;      ↓

Evaluations

&#x20;      ↓

Evidence

&#x20;      ↓

Learning Profile Service

&#x20;      ↓

UserLearningProfile

```



Possible dimensions:



```text

Thinking

&#x20;├── Critical Thinking

&#x20;├── Creativity

&#x20;├── Reasoning

&#x20;├── Perspective Shifting

&#x20;└── Depth



German

&#x20;├── Grammar

&#x20;├── Vocabulary

&#x20;├── Naturalness

&#x20;├── Sentence Structure

&#x20;└── Advanced Expression

```



The profile should not be manually maintained as the source of truth.



\---



\# 30. User Activity



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



\---



\# 31. Complete Learning Journey



The system must preserve historical learning data.



It should not store only the latest score.



Example:



```text

MindQuest 1

&#x20;├── Responses

&#x20;├── Thinking Evaluations

&#x20;├── German Evaluations

&#x20;└── Reflection



MindQuest 2

&#x20;├── Responses

&#x20;├── Thinking Evaluations

&#x20;├── German Evaluations

&#x20;└── Reflection



MindQuest 3

&#x20;└── ...



&#x20;         ↓



Derived Learning Profile

```



This enables progress analysis over time.



\---



\# 32. API Design



The initial API should remain small.



\## MindQuest



```http

POST   /api/v1/mindquests

GET    /api/v1/mindquests

GET    /api/v1/mindquests/{id}

POST   /api/v1/mindquests/{id}/start

POST   /api/v1/mindquests/{id}/responses

POST   /api/v1/mindquests/{id}/advance

GET    /api/v1/mindquests/{id}/reflection

```



\## Learning



```http

GET /api/v1/users/{user\_id}/learning-profile

GET /api/v1/users/{user\_id}/activities

GET /api/v1/users/{user\_id}/mindquests

```



The API should expose use cases rather than internal implementation details.



\---



\# 33. Response Processing Flow



When the user submits a response:



```text

POST /mindquests/{id}/responses

&#x20;               │

&#x20;               ▼

&#x20;       MindQuestService

&#x20;               │

&#x20;               ▼

&#x20;        Validate State

&#x20;               │

&#x20;               ▼

&#x20;       Persist User Response

&#x20;               │

&#x20;       ┌───────┴────────┐

&#x20;       ▼                ▼

Thinking Evaluator   German Evaluator

&#x20;       │                │

&#x20;       └───────┬────────┘

&#x20;               ▼

&#x20;            Evidence

&#x20;               │

&#x20;               ▼

&#x20;            Feedback

&#x20;               │

&#x20;               ▼

&#x20;       Next Challenge

&#x20;               │

&#x20;               ▼

&#x20;       Persist MindQuest

&#x20;               │

&#x20;               ▼

&#x20;         API Response

```



\---



\# 34. Parallel Evaluation



Thinking and German evaluation are independent.



Python async execution should therefore allow parallel evaluation.



Conceptually:



```python

thinking\_task = evaluate\_thinking(...)

german\_task = evaluate\_german(...)



thinking, german = await asyncio.gather(

&#x20;   thinking\_task,

&#x20;   german\_task,

)

```



This reduces overall response latency compared with sequential evaluation.



\---



\# 35. Failure Handling



AI failures must not corrupt the MindQuest.



Example:



```text

User Response

&#x20;     ↓

Persist Response

&#x20;     ↓

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



\---



\# 36. Frontend Architecture



The frontend uses:



\* Next.js

\* TypeScript

\* React

\* Tailwind CSS



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



\---



\# 37. MindQuest UI Components



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

&#x20;   ├── ThinkingReflection

&#x20;   ├── GermanReflection

&#x20;   └── ProgressComparison

```



The frontend structure mirrors the product domain.



\---



\# 38. Frontend State



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



\---



\# 39. V1 Interaction Model



The initial interaction is synchronous from the user's perspective.



```text

User writes response

&#x20;       ↓

Submit

&#x20;       ↓

Thinking evaluation

\+

German evaluation

&#x20;       ↓

Feedback

&#x20;       ↓

Next challenge

```



The system may internally perform multiple asynchronous operations, but the user experiences one coherent turn.



\---



\# 40. Docker Architecture



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

&#x20;  │

&#x20;  ▼

OpenRouter

```



No local LLM infrastructure is required for V1.



\---



\# 41. Configuration



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



\---



\# 42. Testing Architecture



Testing is divided into three levels.



```text

tests/

├── unit/

├── integration/

└── evaluation/

```



\## Unit Tests



Test:



\* Domain rules

\* State transitions

\* Hat Contracts

\* Evaluation calculations

\* Learning profile calculations



No real LLM calls.



\## Integration Tests



Test:



\* FastAPI

\* PostgreSQL

\* Repositories

\* MindQuest workflows

\* AI gateway integration using mocks where appropriate



\## Evaluation Tests



Test real AI behavior against controlled datasets.



\---



\# 43. Evaluation Harness



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



\### Thinking



\* Hat adherence accuracy

\* Evaluation consistency

\* Score stability

\* False positives

\* False negatives



\### German



\* Correction accuracy

\* Grammar detection

\* Naturalness detection

\* Vocabulary assessment

\* Score consistency



\### System



\* Latency

\* Cost

\* Model performance

\* Prompt regression



\---



\# 44. Model and Prompt Regression



The architecture should make it possible to compare:



```text

Model A + Prompt V1

&#x20;       vs

Model A + Prompt V2

```



or:



```text

Model A

&#x20;  vs

Model B

```



against the same evaluation dataset.



This makes the AI system measurable rather than relying only on subjective impressions.



\---



\# 45. Security Boundaries



Even though authentication is out of scope for V1, important boundaries should exist.



OpenRouter credentials:



```text

Browser

&#x20;  X

OpenRouter API Key



Backend

&#x20;  ↓

OpenRouter

```



The browser must never receive the OpenRouter API key.



AI prompts should also be treated as server-side implementation details.



\---



\# 46. Observability



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



\* failures

\* latency

\* model behavior

\* token/cost trends



\---



\# 47. Architectural Principles



LinguaMentis follows these principles:



\### Principle 1 — Application owns state



The LLM never owns authoritative application state.



\### Principle 2 — Agents are bounded



Each agent has a clear Hat Contract.



\### Principle 3 — Agents are not evaluators



The agent that challenges the user should not judge its own performance.



\### Principle 4 — Thinking and German are independent



They have separate scores, rubrics, evidence, and evaluation pipelines.



\### Principle 5 — Structured AI



Important AI interactions use typed structured outputs.



\### Principle 6 — Provider independence



Agents depend on `LLMClient`, not OpenRouter.



\### Principle 7 — Evidence over scores



Evaluation must explain why a score was given.



\### Principle 8 — Domain first



Business rules belong in the domain/application layers.



\### Principle 9 — Preserve the journey



Historical MindQuests and evaluations are retained.



\### Principle 10 — Simplicity first



Do not introduce distributed infrastructure until the product requires it.



\---



\# 48. Explicitly Out of Scope for V1



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



\---



\# 49. Future Evolution



The architecture allows future evolution without changing the core domain.



Possible future additions:



```text

&#x20;               LinguaMentis V1

&#x20;                      │

&#x20;            ┌─────────┴─────────┐

&#x20;            ▼                   ▼

&#x20;       Voice Layer        Advanced Analytics

&#x20;            │                   │

&#x20;            ▼                   ▼

&#x20;         STT/TTS          Learning Insights

&#x20;            │

&#x20;            ▼

&#x20;    Speaking Evaluation

```



If scale eventually requires it, individual capabilities can later be extracted from the modular monolith.



The initial architecture should not assume that extraction is necessary.



\---



\# 50. First Vertical Slice



The first implementation should focus on one complete Black Hat experience.



```text

Blue Agent

&#x20;     ↓

Select Topic

&#x20;     ↓

Black Hat Agent

&#x20;     ↓

Generate Challenge

&#x20;     ↓

User Response

&#x20;     ↓

Thinking Evaluator

&#x20;     +

German Evaluator

&#x20;     ↓

Evidence

&#x20;     ↓

Feedback

&#x20;     ↓

Next Challenge

&#x20;     ↓

Repeat

&#x20;     ↓

Blue Final Reflection

```



This validates the most important architectural boundaries before implementing all six hats.



\---



\# 51. Recommended Implementation Order



```text

1\. Project setup

&#x20;      ↓

2\. PostgreSQL + SQLAlchemy + Alembic

&#x20;      ↓

3\. Domain entities

&#x20;      ↓

4\. MindQuest state machine

&#x20;      ↓

5\. Hat Contracts

&#x20;      ↓

6\. AI/Pydantic contracts

&#x20;      ↓

7\. LLM Gateway

&#x20;      ↓

8\. OpenRouter integration

&#x20;      ↓

9\. BlackHatAgent

&#x20;      ↓

10\. ThinkingEvaluator

&#x20;      ↓

11\. GermanEvaluator

&#x20;      ↓

12\. Evidence persistence

&#x20;      ↓

13\. MindQuest Engine

&#x20;      ↓

14\. FastAPI endpoints

&#x20;      ↓

15\. Next.js MindQuest UI

&#x20;      ↓

16\. Complete Black Hat vertical slice

&#x20;      ↓

17\. Remaining five hats

&#x20;      ↓

18\. Blue orchestration

&#x20;      ↓

19\. Gamification

&#x20;      ↓

20\. Evaluation Harness

&#x20;      ↓

21\. Voice

```



\---



\# 52. Final Architecture Statement



LinguaMentis is a \*\*modular monolith with an AI-native domain architecture\*\*.



Its core architecture can be summarized as:



```text

Next.js

&#x20;  │

&#x20;  ▼

FastAPI

&#x20;  │

&#x20;  ▼

Application Layer

&#x20;  │

&#x20;  ├───────────────┐

&#x20;  ▼               ▼

MindQuest       Evaluation

Engine          Pipeline

&#x20;  │               │

&#x20;  ▼               ├── Thinking Evaluator

Agents             └── German Evaluator

&#x20;  │

&#x20;  ▼

AI Gateway

&#x20;  │

&#x20;  ▼

OpenRouter

&#x20;  │

&#x20;  ▼

PostgreSQL

```



The most important architectural rule is:



> \*\*LinguaMentis is an AI-enabled application, not an LLM-controlled application.\*\*



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



