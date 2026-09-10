# LinguaMentis

## Product Requirements Document

**Version:** 1.0
**Status:** Draft
**Target:** B2–C1 German learners
**Primary Experience:** MindQuest

---

# 1. Product Vision

**LinguaMentis** is a gamified AI debate experience that combines **German language development** with **structured thinking development** using Edward de Bono's **Six Thinking Hats** methodology.

The product is not intended to be a traditional German language course or an AI chatbot.

Instead, LinguaMentis creates an intellectual environment where users must **think, reason, challenge ideas, express opinions, and explore different perspectives — in German**.

### Core Philosophy

> **Language is the medium. Thinking is the skill. Perspective is the method. Growth is the outcome.**

The fundamental learning loop is:

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

LinguaMentis should make the user feel that they are developing both:

* their ability to **think more effectively**
* their ability to **express complex thoughts naturally in German**

---

# 2. One-Sentence Product Definition

> **LinguaMentis is a gamified AI debate experience that uses Six Thinking Hats to help B2/C1 German learners develop stronger thinking skills while learning to express complex ideas naturally in German.**

---

# 3. Target Users

Primary users:

* German learners at **B2 or C1**
* Users who want to become more confident discussing complex topics
* Users preparing for advanced German communication
* Users interested in critical thinking, creativity, discussion, and argumentation
* Professionals who need German for intellectually demanding conversations

The product should assume that the user can already communicate in German.

LinguaMentis is therefore **not primarily vocabulary memorization or grammar training**.

---

# 4. Core Product Concept — MindQuest

A **MindQuest** is one complete intellectual exploration around a topic.

Example:

> **MindQuest:** Sollte KI in Unternehmen stärker reguliert werden?

The user explores the topic through different thinking perspectives represented by the Six Thinking Hats.

A MindQuest contains:

* Topic
* Target language level
* Hat rounds
* Challenges
* User responses
* Thinking evaluations
* German evaluations
* Evidence
* Feedback
* Recommendations
* Progress
* Final reflection

A MindQuest should feel like an intellectual challenge rather than a lesson.

---

# 5. Six Thinking Hats

LinguaMentis uses six distinct thinking modes.

## 5.1 White Hat — Information

Focus:

* Facts
* Information
* Evidence
* Known information
* Missing information
* Questions about what is known or unknown

The White Hat should encourage the user to separate:

> What do we know?

from:

> What do we assume?

---

## 5.2 Red Hat — Feelings

Focus:

* Feelings
* Intuition
* Emotional reactions
* Gut feeling
* Personal impressions

The Red Hat allows the user to express reactions without requiring logical justification for every feeling.

---

## 5.3 Black Hat — Critical Thinking

Focus:

* Risks
* Weaknesses
* Problems
* Negative consequences
* Potential failure
* Hidden assumptions

The Black Hat should challenge the user's thinking.

It should encourage questions such as:

> What could go wrong?

> What is the biggest risk?

> What assumption might be wrong?

The Black Hat should **not primarily propose solutions or benefits**.

---

## 5.4 Yellow Hat — Benefits

Focus:

* Benefits
* Opportunities
* Positive consequences
* Value
* Potential advantages

The Yellow Hat explores:

> Why could this work?

> What could be valuable?

> What opportunities could this create?

---

## 5.5 Green Hat — Creativity

Focus:

* New ideas
* Alternatives
* Unusual possibilities
* Creative solutions
* New perspectives
* Experiments

The Green Hat encourages the user to move beyond obvious answers.

---

## 5.6 Blue Hat — Process and Orchestration

The Blue Hat is fundamentally different.

It manages the **thinking process itself**.

The Blue Agent:

* Starts the MindQuest
* Introduces the topic
* Selects or manages the next hat
* Explains the current challenge
* Coordinates the experience
* Tracks progress
* Determines whether a thinking phase has been sufficiently explored
* Transitions between hats
* Maintains the overall direction
* Detects completion
* Produces the final reflection

The Blue Agent is therefore the **orchestrator**, not the primary evaluator.

It must not replace the thinking performed by the other hats.

---

# 6. Core MindQuest Flow

```text
Start MindQuest
       ↓
Choose / Receive Topic
       ↓
Blue Agent Introduces Challenge
       ↓
Hat Becomes Active
       ↓
Hat Agent Challenges User
       ↓
User Responds in German
       ↓
Thinking Evaluation
       +
German Evaluation
       ↓
Evidence + Feedback
       ↓
Recommendation / Improvement
       ↓
Next Challenge
       ↓
Next Hat
       ↓
All Hats Explored
       ↓
Blue Final Reflection
       ↓
MindQuest Completed
```

The exact order and number of challenges can be controlled by the Blue Agent within explicit application rules.

---

# 7. Debate Experience

LinguaMentis should behave more like an intelligent debate partner than a teacher.

The AI should:

* Ask challenging questions
* Push the user's reasoning
* Challenge assumptions
* Request clarification
* Encourage deeper thinking
* Introduce alternative perspectives
* Detect weak reasoning
* Encourage specificity
* Keep the user cognitively engaged

The AI should avoid turning every interaction into a grammar lesson.

For example, if the user gives a weak Black Hat argument:

> KI ist gefährlich.

The system should first challenge the thinking:

> **Thinking:** Why is it dangerous? Identify a specific risk and explain what consequence could result from it.

Only afterward should language feedback be given.

---

# 8. Evaluation Philosophy

LinguaMentis maintains **two completely independent evaluation dimensions**.

They must never be collapsed into one score.

```text
                User Response
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
Thinking Evaluation      German Evaluation
          │                     │
          ↓                     ↓
Thinking Score           German Score
          │                     │
          ↓                     ↓
Thinking Evidence        German Evidence
```

---

# 9. Thinking Quality Evaluation

Thinking Quality measures the quality of the user's thinking within the active hat.

Possible dimensions include:

* Hat adherence
* Relevance
* Depth
* Reasoning
* Specificity
* Causal reasoning
* Consequence analysis
* Creativity where applicable
* Perspective awareness

The dimensions depend on the active hat.

### Example — Black Hat

A strong response should:

* Identify a genuine risk
* Explain why it is a risk
* Describe a possible consequence
* Remain focused on critical analysis
* Avoid switching into solution mode

---

# 10. German Quality Evaluation

German Quality evaluates the user's German independently.

Possible dimensions:

* Grammar
* Vocabulary
* Sentence structure
* Naturalness
* Fluency
* B2/C1 appropriateness
* Precision of expression

The German evaluator should distinguish between:

* grammatically incorrect
* grammatically correct but unnatural
* simple but acceptable
* sophisticated and natural
* inappropriate vocabulary
* appropriate advanced vocabulary

---

# 11. Evidence-Based Evaluation

Scores alone are not sufficient.

Every important evaluation should contain **first-class evidence** explaining why the score was given.

## Thinking Evidence

Examples:

* Identified a genuine risk
* Explained a causal relationship
* Stayed within Black Hat
* Challenged an assumption
* Provided a specific consequence
* Used an alternative perspective

## German Evidence

Examples:

* Correct use of conditional structure
* Appropriate B2 vocabulary
* Clear causal construction
* Incorrect word order
* Unnatural sentence construction
* Vocabulary too simple for C1
* More natural alternative expression available

The evidence should be persisted and become part of the user's learning journey.

---

# 12. Feedback Order

When both thinking and language problems exist, LinguaMentis should prioritize **thinking first**.

Example:

> **Thinking:** Your argument describes a benefit rather than a risk. Stay in Black Hat and identify a possible negative consequence.
>
> **German:** “Das könnte die Kosten erhöhen” is a more natural way to express the consequence.

This prevents the user from becoming focused on grammar while failing the intellectual task.

---

# 13. Target Language Level

LinguaMentis initially supports:

* B2
* C1

The selected level influences:

### Agent Interaction

* Question complexity
* Vocabulary
* Expected reasoning depth
* Follow-up questions
* Challenge difficulty

### German Evaluation

* Grammar expectations
* Vocabulary expectations
* Sentence complexity
* Naturalness
* Precision
* Appropriate level of sophistication

The system should not simply penalize B2 users for failing to produce C1-level language.

---

# 14. Hat Contracts

Each Hat Agent should operate under an explicit contract.

A Hat Contract defines:

* Goal
* What the agent should do
* What the agent should not do
* Thinking dimensions
* Question strategy
* Feedback strategy

### Example — Black Hat Contract

**Goal**

Identify risks, weaknesses, assumptions, and negative consequences.

**Should**

* Challenge assumptions
* Identify potential problems
* Explore consequences
* Ask for evidence
* Encourage specificity

**Should NOT**

* Propose solutions
* Focus on benefits
* Express personal emotions
* Switch unnecessarily into another thinking mode

**Thinking Dimensions**

* Risk identification
* Causal reasoning
* Consequence analysis
* Specificity
* Hat adherence

These contracts provide behavioral constraints for the agents.

---

# 15. Blue Agent Responsibilities

The Blue Agent is responsible for the lifecycle of the MindQuest.

It should:

1. Start the MindQuest
2. Introduce the topic
3. Explain the current thinking mode
4. Coordinate the active Hat Agent
5. Monitor progress
6. Decide when a phase is sufficiently explored
7. Transition to another hat
8. Detect completion
9. Initiate final reflection
10. Produce the final synthesis

The Blue Agent must not become the user's primary source of thinking.

The user should perform the intellectual work.

---

# 16. Application State Management

The application, not the LLM, owns the authoritative state.

## Application owns

* MindQuest state
* Topic
* Target level
* Current hat
* Turn
* User responses
* Scores
* Evaluation results
* Completion state
* Progress

## LLM owns

* Questions
* Challenges
* Evaluations
* Feedback
* Recommendations
* Final synthesis

The LLM must never be treated as the authoritative source of application state.

---

# 17. MindQuest State Machine

A MindQuest should use an explicit state machine.

Example:

```text
CREATED
   ↓
TOPIC_SELECTED
   ↓
IN_PROGRESS
   ↓
HAT_ACTIVE
   ↓
HAT_COMPLETED
   ↓
HAT_ACTIVE
   ↓
...
   ↓
ALL_HATS_COMPLETED
   ↓
FINAL_EVALUATION
   ↓
COMPLETED
```

State transitions should be controlled by the application.

The LLM may recommend or provide information relevant to a transition, but it should not directly mutate authoritative application state.

---

# 18. Domain Model

LinguaMentis should persist the complete learning journey.

Conceptually:

```text
User
 ├── MindQuests
 │    ├── HatRounds
 │    ├── Turns
 │    ├── Responses
 │    ├── ThinkingEvaluations
 │    ├── GermanEvaluations
 │    └── Evidence
 │
 └── Activities
```

Across the complete journey:

```text
User
 ├── MindQuests
 ├── Activities
 └──────────────→ UserLearningProfile
```

---

# 19. Core Entities

Initial domain entities:

* `User`
* `MindQuest`
* `HatRound`
* `Turn`
* `ThinkingEvaluation`
* `GermanEvaluation`
* `Evidence`
* `UserActivity`
* `FinalReflection`

A future derived entity:

* `UserLearningProfile`

---

# 20. User

A `User` entity exists even in V1.

Authentication and user-management functionality are explicitly outside the initial scope.

V1 assumes that a predefined user exists.

All user-specific data must be associated with `UserId`.

This allows the architecture to support multiple users later without redesigning the core domain model.

---

# 21. User Learning Profile

The `UserLearningProfile` is a **derived profile**.

It should be calculated from the accumulated learning journey rather than manually maintained.

It may eventually contain insights such as:

```text
Thinking
 ├── Critical Thinking
 ├── Creativity
 ├── Perspective Shifting
 ├── Reasoning
 └── Depth

German
 ├── Grammar
 ├── Vocabulary
 ├── Naturalness
 ├── Sentence Structure
 └── Advanced Expression
```

The profile should reflect patterns across multiple MindQuests rather than a single interaction.

---

# 22. Activity History

Activities preserve the chronology of the learning journey.

Possible activity types:

* `MindQuestStarted`
* `TopicSelected`
* `HatSelected`
* `ResponseSubmitted`
* `ThinkingEvaluated`
* `GermanEvaluated`
* `HatCompleted`
* `AchievementUnlocked`
* `MindQuestCompleted`

`UserActivity` is not the primary source of truth for domain state.

Domain entities remain authoritative.

---

# 23. Complete Learning Journey

LinguaMentis should preserve the user's complete journey.

The system should not store only:

> Current score = 84

Instead, it should preserve:

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

This enables meaningful progress analysis.

---

# 24. Final Reflection

At the end of a MindQuest, the Blue Agent produces a final reflection.

The reflection contains two independent sections.

## Thinking Reflection

* Overall thinking performance
* Strongest thinking modes
* Weakest thinking modes
* Evidence
* Important reasoning patterns
* Recommendations
* Progress compared with previous MindQuests

## German Reflection

* Overall German performance
* Grammar strengths
* Vocabulary strengths/weaknesses
* Naturalness
* Important corrections
* Recommended expressions
* B2/C1 recommendations
* Progress compared with previous MindQuests

---

# 25. Gamification

Gamification should reinforce **intellectual development**, not merely reward activity.

Potential achievements:

* **Hat Discipline**
* **Critical Thinker**
* **Idea Generator**
* **Perspective Shifter**
* **Deep Thinker**
* **German Debater**

Possible score dimensions:

```text
THINKING
████████████████░░░░ 82

GERMAN
███████████████░░░░░ 76
```

The two scores remain independent.

The goal is for the user to feel:

> "I am becoming a better thinker who can express complex ideas in German."

Not:

> "I collected more XP."

---

# 26. AI Architecture

Conceptual architecture:

```text
Browser
   ↓
Next.js Application
   ↓
Backend API
   ↓
MindQuest Engine / Orchestrator
   ↓
Agent Registry
   ├── WhiteHatAgent
   ├── RedHatAgent
   ├── BlackHatAgent
   ├── YellowHatAgent
   ├── GreenHatAgent
   └── BlueHatAgent
   ↓
Evaluation Pipeline
   ├── ThinkingEvaluator
   └── GermanEvaluator
   ↓
LLM Gateway
   ↓
OpenRouter
   ↓
Selected Models
```

Agents should not know that OpenRouter is being used.

They communicate through an abstraction such as:

```text
ILLMClient
```

with an implementation such as:

```text
OpenRouterClient
```

This keeps provider details outside the domain and agent logic.

---

# 27. Structured AI Outputs

Important AI interactions should use structured outputs.

Examples:

* `HatChallenge`
* `ThinkingEvaluation`
* `GermanEvaluation`
* `HatFeedback`
* `FinalReflection`

Example conceptual evaluation:

```text
ThinkingEvaluation
 ├── Score
 ├── Dimensions
 ├── HatAdherence
 ├── Evidence[]
 ├── Strengths[]
 ├── Weaknesses[]
 └── Recommendations[]

GermanEvaluation
 ├── Score
 ├── Dimensions
 ├── Evidence[]
 ├── Corrections[]
 ├── Strengths[]
 ├── Weaknesses[]
 └── Recommendations[]
```

This makes AI behavior easier to validate, persist, test, and evolve.

---

# 28. Agents vs Evaluators

Agents and evaluators must remain conceptually separate.

For example:

```text
BlackHatAgent
       ↓
Challenges the user

User Response
       ↓
ThinkingEvaluator
       ↓
Evaluates Black Hat adherence

       +

GermanEvaluator
       ↓
Evaluates German
```

The Black Hat Agent should not be responsible for judging whether its own interaction was successful.

This separation improves evaluation reliability and enables independent testing.

---

# 29. Evaluation Harness

One of the major technical differentiators of LinguaMentis is an **evaluation harness**.

The system should evaluate not only the user, but eventually the quality of its own evaluators.

A fixed evaluation dataset should contain examples of:

* B2 responses
* C1 responses
* Good hat adherence
* Poor hat adherence
* Strong reasoning
* Weak reasoning
* Grammar mistakes
* Vocabulary problems
* Natural German
* Unnatural German
* Mixed-quality responses

The harness can evaluate:

### Thinking Evaluation

* Hat adherence accuracy
* Reasoning evaluation consistency
* Score stability
* False positives
* False negatives

### German Evaluation

* Correction accuracy
* Grammar detection accuracy
* Naturalness detection
* Vocabulary assessment
* Score consistency

### System Performance

* Latency
* Cost
* Model performance
* Prompt regression

Eventually:

> The evaluator itself becomes something that can be systematically evaluated.

---

# 30. Voice

Voice is intentionally not part of the first implementation.

### V1

Text-based interaction.

### Shortly after V1

Voice input using speech-to-text.

Future evaluation dimensions may include:

* Pronunciation
* Speaking fluency
* Pacing
* Pauses
* Intonation

These should remain separate from the initial German Quality score.

---

# 31. Technology Stack — V1

## Frontend

* Next.js
* TypeScript
* React
* Tailwind CSS

## Backend

* Python
* FastAPI

## AI

* OpenRouter
* Free/low-cost models during development
* Structured LLM outputs

## Database

* PostgreSQL

## V1 Architecture Principle

Keep the system intentionally simple.

Do **not** introduce infrastructure merely because it may be useful in a future version.

---

# 32. Explicitly Out of Scope for V1

The following are not required initially:

* Authentication system
* User-management UI
* Kafka
* Microservices
* Event sourcing
* Vector database
* Complex recommendation engine
* Mobile application
* Payments
* Subscription management
* Distributed workflow infrastructure
* Real-time voice interaction
* Advanced pronunciation analysis

The objective is to build a strong vertical slice first.

---

# 33. Development Strategy

Development should proceed incrementally.

## Phase 1 — Product Methodology

Define:

* Six Hats
* Hat Contracts
* Thinking rubric
* German rubric
* MindQuest lifecycle

## Phase 2 — AI Contracts

Define structured contracts for:

* Challenges
* Thinking evaluation
* German evaluation
* Feedback
* Final reflection

## Phase 3 — MindQuest State Machine

Implement:

```text
CREATED
→ TOPIC_SELECTED
→ HAT_ACTIVE
→ HAT_COMPLETED
→ ...
→ COMPLETED
```

## Phase 4 — First Vertical Slice

Implement one complete experience using Black Hat:

```text
Blue Agent
      ↓
Topic
      ↓
Black Hat Agent
      ↓
Question
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
...
      ↓
Blue Final Reflection
```

This vertical slice should be working end-to-end before implementing all six hats.

## Phase 5 — Six Hats

Implement:

* White
* Red
* Black
* Yellow
* Green
* Blue

## Phase 6 — Blue Orchestration

Implement complete MindQuest orchestration and final synthesis.

## Phase 7 — Persistence and Learning Journey

Persist:

* MindQuests
* Turns
* Responses
* Evaluations
* Evidence
* Activities
* Reflections

## Phase 8 — Gamification

Add:

* Achievements
* Progress
* Thinking trends
* German trends

## Phase 9 — Voice

Add speech-to-text and eventually speaking-specific evaluation.

## Phase 10 — Evaluation Harness

Build systematic testing of:

* Agents
* Evaluators
* Prompts
* Models
* Regression behavior

---

# 34. Product Success Criteria

LinguaMentis should succeed if users:

1. Think more deeply about complex topics.
2. Become better at switching perspectives.
3. Produce longer and more sophisticated German responses.
4. Become more comfortable discussing abstract topics.
5. Understand their thinking weaknesses.
6. Understand their German weaknesses.
7. Can see measurable progress across MindQuests.
8. Feel challenged rather than merely taught.

Technical success also requires:

* Reliable state management
* Consistent structured AI outputs
* Independent evaluation pipelines
* Persisted evidence
* Reproducible evaluation
* Regression testing
* Reasonable latency and cost

---

# 35. Core Product Principle

LinguaMentis should never become:

> **A German-learning chatbot with Six Thinking Hats added to it.**

It should become:

> **An intellectual experience in which German is the language through which the user learns to think, argue, question, and express ideas.**

The distinction is fundamental.

---

# 36. Final Product Definition

**LinguaMentis**

> **Think through language.**

A user enters a **MindQuest**, explores a complex topic through the Six Thinking Hats, responds in German, receives independent feedback on both **thinking quality** and **German quality**, and gradually builds a measurable intellectual and linguistic learning journey.
