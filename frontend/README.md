\# LinguaMentis Frontend



> \*\*Think through language.\*\*



The LinguaMentis frontend is the interactive web experience for MindQuest.



It provides the learner with a focused environment to:



\* explore a topic

\* think through the Six Thinking Hats

\* respond in German

\* receive independent Thinking and German evaluations

\* track progress

\* review evidence and corrections

\* complete the final reflection

\* explore their learning journey



The frontend is intentionally thin.



\*\*The backend owns MindQuest state.\*\*



\---



\# Architecture



```text

┌──────────────────────────────────────────┐

│              Next.js App                 │

│                                          │

│  Pages / Routes                          │

│       ↓                                  │

│  MindQuest Components                    │

│       ↓                                  │

│  API Services                            │

└──────────────────┬───────────────────────┘

&#x20;                  │ HTTP

&#x20;                  ▼

&#x20;       ┌──────────────────────┐

&#x20;       │   LinguaMentis API   │

&#x20;       └──────────────────────┘

```



The frontend owns:



\* UI state

\* response drafts

\* dialogs

\* loading states

\* animations

\* display preferences

\* temporary interaction state



The backend owns:



\* MindQuest lifecycle

\* current Hat

\* turns

\* responses

\* scores

\* evaluations

\* completion

\* learning history



\---



\# Technology Stack



| Area            | Technology                            |

| --------------- | ------------------------------------- |

| Framework       | Next.js                               |

| Language        | TypeScript                            |

| UI              | React                                 |

| Styling         | Tailwind CSS                          |

| API             | LinguaMentis FastAPI backend          |

| State           | Server state + local UI state         |

| Package Manager | npm / pnpm / project-selected manager |



The frontend should remain lightweight and avoid unnecessary state-management infrastructure in V1.



\---



\# Project Structure



```text

frontend/

├── package.json

├── tsconfig.json

├── next.config.ts

├── README.md

│

└── src/

&#x20;   ├── app/

&#x20;   │   ├── page.tsx

&#x20;   │   │

&#x20;   │   ├── mindquests/

&#x20;   │   │   ├── page.tsx

&#x20;   │   │   └── \[id]/

&#x20;   │   │       ├── page.tsx

&#x20;   │   │       └── reflection/

&#x20;   │   │           └── page.tsx

&#x20;   │   │

&#x20;   │   ├── learning/

&#x20;   │   │   └── page.tsx

&#x20;   │   │

&#x20;   │   └── history/

&#x20;   │       └── page.tsx

&#x20;   │

&#x20;   ├── components/

&#x20;   │   ├── mindquest/

&#x20;   │   │   ├── MindQuestHeader.tsx

&#x20;   │   │   ├── MindQuestProgress.tsx

&#x20;   │   │   ├── ChallengeCard.tsx

&#x20;   │   │   ├── ResponseEditor.tsx

&#x20;   │   │   └── MindQuestTimeline.tsx

&#x20;   │   │

&#x20;   │   ├── hats/

&#x20;   │   │   ├── HatIndicator.tsx

&#x20;   │   │   ├── HatProgress.tsx

&#x20;   │   │   └── HatChallenge.tsx

&#x20;   │   │

&#x20;   │   ├── evaluation/

&#x20;   │   │   ├── ThinkingEvaluation.tsx

&#x20;   │   │   ├── GermanEvaluation.tsx

&#x20;   │   │   ├── EvidenceList.tsx

&#x20;   │   │   ├── CorrectionList.tsx

&#x20;   │   │   └── RecommendationList.tsx

&#x20;   │   │

&#x20;   │   ├── reflection/

&#x20;   │   │   ├── ThinkingReflection.tsx

&#x20;   │   │   ├── GermanReflection.tsx

&#x20;   │   │   └── ProgressComparison.tsx

&#x20;   │   │

&#x20;   │   └── ui/

&#x20;   │

&#x20;   ├── services/

&#x20;   │   └── api/

&#x20;   │

&#x20;   ├── types/

&#x20;   │

&#x20;   └── lib/

```



\---



\# Core Experience



The primary frontend experience is the MindQuest page.



```text

┌─────────────────────────────────────────┐

│ MindQuest                               │

│ Topic: Should AI be regulated?          │

├─────────────────────────────────────────┤

│                                         │

│       CURRENT HAT: BLACK                │

│                                         │

│  What could go wrong?                   │

│                                         │

│  ┌───────────────────────────────────┐  │

│  │ Challenge                         │  │

│  │ Welche konkreten Risiken ...?     │  │

│  └───────────────────────────────────┘  │

│                                         │

│  ┌───────────────────────────────────┐  │

│  │ Your response...                  │  │

│  │                                   │  │

│  └───────────────────────────────────┘  │

│                                         │

│             \[ Submit Response ]          │

│                                         │

├─────────────────────────────────────────┤

│ Progress: White ✓  Red ✓  Black ●       │

│          Yellow ○  Green ○              │

└─────────────────────────────────────────┘

```



The interface should keep the learner focused on the current thinking task.



\---



\# MindQuest Page



The MindQuest page is the core interaction surface.



It should communicate:



\* current topic

\* current Hat

\* current challenge

\* learner response

\* progress

\* evaluation state

\* next action



The page should avoid unnecessary UI elements that distract from thinking.



\---



\# Six Hats UI



The Six Hats should be visually distinguishable while keeping the interface cognitively simple.



```text

White ✓

Red ✓

Black ●

Yellow ○

Green ○

Blue

```



Possible states:



```text

○ Not started

● Active

✓ Completed

```



The frontend should receive the authoritative state from the backend.



It should not independently decide which Hat is active.



\---



\# Challenge Card



`ChallengeCard` displays the current AI-generated challenge.



It should show:



\* Hat

\* question

\* instruction

\* difficulty when useful



Example:



```text

BLACK HAT



Bleibe beim Black Hat und konzentriere dich auf

mögliche negative Konsequenzen.



Welche konkreten Risiken könnten entstehen,

wenn Unternehmen KI stärker einsetzen?

```



The frontend should not generate or modify the challenge.



\---



\# Response Editor



`ResponseEditor` allows the learner to write their response in German.



Responsibilities:



\* text input

\* character/word information when useful

\* submit action

\* loading state

\* validation

\* error state

\* draft preservation during UI transitions



The response should be submitted to the backend before evaluation begins.



\---



\# Evaluation UI



Evaluation should clearly separate the two dimensions.



```text

┌─────────────────────────────────────────┐

│ Thinking Quality                  78/100│

├─────────────────────────────────────────┤

│ Hat Adherence                     82    │

│ Relevance                         90    │

│ Reasoning                         78    │

│ Depth                             68    │

│ Specificity                       74    │

│                                         │

│ Evidence                                │

│ ✓ Identified a concrete risk            │

│ ✓ Explained a causal relationship       │

│                                         │

│ Recommendation                          │

│ Explore the second-order consequence.   │

└─────────────────────────────────────────┘



┌─────────────────────────────────────────┐

│ German Quality                    81/100│

├─────────────────────────────────────────┤

│ Grammar                           88    │

│ Vocabulary                        76    │

│ Sentence Structure                82    │

│ Naturalness                       82    │

│ Level Appropriateness             78    │

│                                         │

│ Corrections                            │

│ ...                                     │

└─────────────────────────────────────────┘

```



The UI must not present these as one combined score.



\---



\# Evidence



Evidence is a first-class UI element.



A score should be understandable.



Instead of:



```text

Thinking: 78

```



show:



```text

Thinking: 78



Why?

✓ Identified a concrete risk.

✓ Explained the causal relationship.

△ Did not explore a second-order consequence.

```



This makes evaluation useful for learning rather than merely gamified scoring.



\---



\# German Corrections



Corrections should be concise and actionable.



Example:



```text

Your sentence:

Das macht einen großen Einfluss.



Better:

Das hat einen großen Einfluss.



Why:

"Einfluss haben" is the natural German collocation.

```



The frontend should display corrections without overwhelming the learner.



\---



\# Feedback Order



The experience should normally follow:



```text

Thinking Feedback

&#x20;      ↓

German Feedback

&#x20;      ↓

Next Challenge

```



This reflects the product philosophy:



> \*\*Thinking first. Language second.\*\*



\---



\# Final Reflection



When all Hats are complete, the frontend displays the Blue Agent's final reflection.



The reflection should contain two independent sections.



\## Thinking



\* overall thinking performance

\* strongest Hats

\* weakest Hats

\* evidence

\* recurring patterns

\* recommendations

\* progress compared with previous MindQuests



\## German



\* overall German performance

\* grammar strengths

\* vocabulary weaknesses

\* naturalness

\* important corrections

\* recommended expressions

\* B2/C1 recommendations

\* progress over time



\---



\# Learning Page



The learning page represents the learner's accumulated development.



Possible sections:



```text

Thinking Development

├── Hat performance

├── Reasoning trends

├── Depth trends

└── Perspective strengths



German Development

├── Grammar

├── Vocabulary

├── Naturalness

└── Level progression

```



The frontend should consume the derived learning profile from the backend.



It should not calculate authoritative learning metrics independently.



\---



\# History Page



The history page shows the learner's complete journey.



Example:



```text

MindQuest History



AI Regulation

Completed

Thinking: 78

German: 81



Remote Work

Completed

Thinking: 84

German: 79



Social Media

Completed

Thinking: 72

German: 85

```



Selecting a MindQuest should allow the learner to revisit:



\* topic

\* Hat progression

\* responses

\* evaluations

\* evidence

\* corrections

\* final reflection



\---



\# API Layer



Frontend API calls should be isolated under:



```text

src/services/api/

```



Example:



```text

services/api/

├── client.ts

├── mindquests.ts

├── turns.ts

├── evaluations.ts

├── users.ts

└── learning.ts

```



Components should not contain raw `fetch()` calls to backend endpoints.



Preferred:



```text

Component

&#x20;   ↓

API Service

&#x20;   ↓

Backend API

```



\---



\# Types



API/domain response types should be centralized under:



```text

src/types/

```



Important types include:



```text

User

MindQuest

HatType

HatRound

Turn

Challenge

ThinkingEvaluation

GermanEvaluation

Evidence

Correction

FinalReflection

LearningProfile

```



Frontend types should reflect backend contracts.



Avoid duplicating business rules in TypeScript.



\---



\# State Management



V1 intentionally keeps state management simple.



\### Backend state



The backend is authoritative for:



\* current Hat

\* current turn

\* MindQuest state

\* scores

\* evaluations

\* completion



\### Frontend state



The frontend owns temporary state such as:



\* response draft

\* modal visibility

\* loading indicators

\* UI animations

\* temporary error state



Conceptually:



```text

Server State

&#x20;   ↓

Backend API

&#x20;   ↓

Frontend View



Local UI State

&#x20;   ↓

React

```



Do not introduce a global state framework unless a concrete requirement appears.



\---



\# Loading States



AI interactions may take time.



The UI should clearly communicate states such as:



```text

Submitting response...

Evaluating your thinking...

Evaluating your German...

Preparing your next challenge...

```



The learner should never be left wondering whether the application is still working.



\---



\# Error Handling



The frontend should handle:



\* network errors

\* backend validation errors

\* MindQuest state conflicts

\* AI evaluation delays/failures

\* unavailable MindQuest

\* failed submissions



A failed evaluation should not imply that the learner's response was lost.



If the response was persisted successfully, the UI should preserve that state.



\---



\# Accessibility



The interface should support:



\* keyboard navigation

\* semantic HTML

\* visible focus states

\* readable contrast

\* accessible form labels

\* screen-reader-friendly feedback

\* clear error messages



The intellectual experience should not depend entirely on visual styling.



\---



\# Responsive Design



The core MindQuest experience should work on:



\* desktop

\* tablet

\* mobile



However, V1 priority is the \*\*desktop/web learning experience\*\*.



Responsive behavior should preserve:



```text

Current Hat

&#x20;     ↓

Challenge

&#x20;     ↓

Response

&#x20;     ↓

Evaluation

```



without unnecessary navigation complexity.



\---



\# Frontend Principles



\### Keep the learner in cognitive mode



The UI should help the learner think rather than distract them.



\### Make the current Hat obvious



The learner should always know:



> What kind of thinking am I doing now?



\### Separate thinking from language



Never visually merge Thinking Quality and German Quality into one score.



\### Show evidence



Scores should be explainable.



\### Keep the interface focused



Avoid unnecessary dashboards during active thinking.



\### Backend is authoritative



Do not duplicate MindQuest business logic in React.



\### Keep V1 simple



Avoid unnecessary:



\* global state frameworks

\* complex design systems

\* real-time infrastructure

\* client-side AI calls

\* AI SDK coupling

\* offline synchronization



unless a real requirement emerges.



\---



\# Security



The OpenRouter API key must never be exposed to the frontend.



AI calls always follow:



```text

Browser

&#x20;  ↓

Backend

&#x20;  ↓

LLM Gateway

&#x20;  ↓

OpenRouter

```



Never:



```text

Browser

&#x20;  ↓

OpenRouter

```



Environment variables containing secrets must remain server-side.



\---



\# Local Development



\## Requirements



Install:



\* Node.js

\* npm or the package manager selected by the project

\* running LinguaMentis backend



\---



\## Install Dependencies



```bash

npm install

```



\---



\## Environment



Create:



```text

.env.local

```



Example:



```env

NEXT\_PUBLIC\_API\_BASE\_URL=http://localhost:8000

```



Only public configuration belongs in `NEXT\_PUBLIC\_\*`.



Never put:



```text

OPENROUTER\_API\_KEY

```



or other server secrets in the frontend environment.



\---



\## Start Development Server



```bash

npm run dev

```



The application should then communicate with the local FastAPI backend.



\---



\# Typical Development Flow



```text

Start PostgreSQL

&#x20;     ↓

Start Backend

&#x20;     ↓

Start Frontend

&#x20;     ↓

Create MindQuest

&#x20;     ↓

Start MindQuest

&#x20;     ↓

Receive Hat Challenge

&#x20;     ↓

Write German response

&#x20;     ↓

Submit

&#x20;     ↓

View Thinking Evaluation

&#x20;     ↓

View German Evaluation

&#x20;     ↓

Continue

```



\---



\# V1 Pages



Initial pages:



```text

/

&#x20;   Landing / Home



/mindquests

&#x20;   MindQuest list



/mindquests/{id}

&#x20;   Active MindQuest



/mindquests/{id}/reflection

&#x20;   Final reflection



/learning

&#x20;   Learning profile



/history

&#x20;   Learning journey

```



\---



\# V1 Vertical Slice



The first frontend vertical slice should support:



```text

MindQuest

&#x20;   ↓

Black Hat

&#x20;   ↓

Challenge

&#x20;   ↓

Response Editor

&#x20;   ↓

Submit

&#x20;   ↓

Thinking Evaluation

&#x20;   ↓

German Evaluation

&#x20;   ↓

Evidence

&#x20;   ↓

Next Challenge

```



This should work end-to-end before building the complete learning dashboard.



\---



\# Related Documents



From the repository root:



```text

README.md

PRD.md

HatContracts.md

EvaluationRubric.md

Architecture.md

```



These define the product vision, cognitive contracts, evaluation methodology, architecture, and overall project.



\---



\# Status



\*\*V1 — Architecture and implementation in progress.\*\*



The immediate priority is a focused, polished MindQuest experience before expanding secondary screens.



\---



\## Product Philosophy



> \*\*Language is the medium.

> Thinking is the skill.

> Perspective is the method.

> Growth is the outcome.\*\*



