# LinguaMentis — Evaluation Rubric

> **Think through language.**

## 1. Purpose

This document defines how LinguaMentis evaluates learner responses during a MindQuest.

The evaluation system measures two fundamentally different capabilities:

1. **Thinking Quality**

2. **German Quality**

These dimensions are evaluated independently.

The purpose of the rubric is to provide:

- consistent evaluation

- explainable scores

- evidence-based feedback

- useful learning recommendations

- stable evaluation across models and prompts

- a foundation for automated evaluation testing and regression analysis

The rubric is a **domain specification**, not an LLM prompt.

---

# 2. Core Evaluation Principle

A learner response is evaluated according to the thinking task they were asked to perform and the German language used to express that thinking.

```text

Learner Response

      │
      ├───────────────────────┐
      ↓                       ↓
Thinking Evaluation      German Evaluation
      │                       │
      ↓                       ↓
Thinking Quality         German Quality
      │                       │
      ↓                       ↓
Evidence                 Evidence

```

The two evaluations must remain independent.

A strong German response does not automatically mean strong thinking.

A strong argument does not automatically mean strong German.

---

# 3. What We Evaluate

For every meaningful learner response:

```text

Thinking Quality
   ├── Hat Adherence
   ├── Relevance
   ├── Reasoning
   ├── Depth
   └── Specificity



German Quality
   ├── Grammar
   ├── Vocabulary
   ├── Sentence Structure
   ├── Naturalness
   └── Level Appropriateness

```

Additional dimensions may apply to particular Hats.

For example:

- Green Hat → creativity

- White Hat → evidence awareness

- Red Hat → emotional clarity

- Blue Hat → synthesis/process awareness

These additional dimensions must not destroy the common evaluation model.

---

# 4. Evaluation Output

The evaluator should return structured data.

Conceptually:

```python

class ThinkingEvaluation(BaseModel):

   score: int



   hat_adherence: int

   relevance: int

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

   sentence_structure: int

   naturalness: int

   level_appropriateness: int



   evidence: list\[Evidence]



   corrections: list\[Correction]



   strengths: list\[str]

   weaknesses: list\[str]

   recommendations: list\[str]

```

The exact implementation may evolve, but the conceptual separation must remain.

---

# 5. Thinking Quality

## 5.1 Definition

Thinking Quality measures how effectively the learner performs the assigned cognitive task.

It does **not** measure German proficiency.

A learner can express a sophisticated idea using imperfect German and still demonstrate high-quality thinking.

---

# 6. Thinking Score

The Thinking Score is expressed on a **0–100 scale**.

Recommended weighting:

| Dimension     |   Weight |
| ------------- | -------: |
| Hat Adherence |      25% |
| Relevance     |      15% |
| Reasoning     |      25% |
| Depth         |      20% |
| Specificity   |      15% |
| **Total**     | **100%** |

Formula:

```text

Thinking Score =

   Hat Adherence × 0.25

 + Relevance × 0.15

 + Reasoning × 0.25

 + Depth × 0.20

 + Specificity × 0.15

```

Each dimension is scored from 0–100.

The final score is rounded to the nearest integer.

---

# 7. Thinking Dimension: Hat Adherence

## Question

> Did the learner actually think within the assigned Hat?

This is the most important dimension because the entire LinguaMentis methodology depends on perspective-specific thinking.

### 90–100 — Excellent

The response strongly embodies the assigned thinking mode.

### 75–89 — Strong

The response clearly follows the Hat with minor contamination.

### 60–74 — Adequate

The response generally follows the Hat but contains noticeable movement toward another perspective.

### 40–59 — Weak

The response partially addresses the Hat but significantly mixes thinking modes.

### 20–39 — Very Weak

The response mostly performs another type of thinking.

### 0–19 — Failure

The response does not meaningfully address the assigned Hat.

---

# 8. Thinking Dimension: Relevance

## Question

> Does the response directly address the current topic and challenge?

High relevance means the learner:

- answers the actual question

- stays on topic

- addresses the assigned problem

- avoids unrelated arguments

Low relevance means:

- changing the subject

- giving generic statements

- repeating unrelated opinions

- avoiding the actual challenge

---

# 9. Thinking Dimension: Reasoning

## Question

> Does the learner explain why their claim is valid?

Reasoning is stronger when the learner establishes relationships such as:

```text

Claim

 ↓

Reason

 ↓

Consequence

```

Example:

Weak:

> KI kann gefährlich sein.

Stronger:

> KI kann gefährlich sein, weil fehlerhafte Empfehlungen automatisch übernommen werden könnten.

Even stronger:

> Wenn Mitarbeiter KI-Ergebnisse ungeprüft übernehmen, könnten Fehler in wichtige Entscheidungen einfließen und dadurch finanzielle Schäden verursachen.

The evaluator should reward causal relationships, not merely longer answers.

---

# 10. Thinking Dimension: Depth

## Question

> Does the learner go beyond the first obvious idea?

Depth includes:

- second-order consequences

- underlying assumptions

- competing factors

- indirect effects

- conditions

- trade-offs

- deeper causal relationships

Example:

```text

First-order:

KI spart Zeit.



Second-order:

Dadurch können Mitarbeiter mehr Aufgaben übernehmen.



Third-order:

Das könnte jedoch langfristig dazu führen, dass Unternehmen

mit weniger Mitarbeitern dieselbe Arbeitsmenge erwarten.

```

The third statement demonstrates greater depth.

---

# 11. Thinking Dimension: Specificity

## Question

> Is the learner's thinking concrete enough to be meaningful?

Weak:

> Es gibt viele Risiken.

Strong:

> Ein Risiko besteht darin, dass Mitarbeiter falsche KI-Ergebnisse übernehmen und dadurch fehlerhafte Entscheidungen treffen.

Specific thinking identifies:

- who

- what

- why

- how

- when

- consequence

where appropriate.

---

# 12. Hat-Specific Thinking Dimensions

The common dimensions remain applicable, but individual Hats may require additional interpretation.

## White Hat

Additional focus:

- fact/assumption distinction

- evidence awareness

- information completeness

- uncertainty

## Red Hat

Additional focus:

- emotional clarity

- intuition awareness

- authenticity

- distinction between feelings and facts

## Black Hat

Additional focus:

- risk identification

- negative consequences

- assumption challenges

- failure conditions

## Yellow Hat

Additional focus:

- benefit identification

- value creation

- positive consequences

- realistic opportunity

## Green Hat

Additional focus:

- originality

- variety

- idea generation

- combinations

- unconventional thinking

## Blue Hat

Additional focus:

- synthesis

- process awareness

- perspective integration

- prioritization

- next-step reasoning

These dimensions may be represented explicitly in future versions of the evaluator.

---

# 13. German Quality

## 13.1 Definition

German Quality measures how effectively the learner communicates their thinking in German.

It evaluates the language independently from the intellectual quality of the response.

---

# 14. German Score

The German Score is expressed on a **0–100 scale**.

Recommended weighting:

| Dimension             |   Weight |
| --------------------- | -------: |
| Grammar               |      25% |
| Vocabulary            |      20% |
| Sentence Structure    |      20% |
| Naturalness           |      20% |
| Level Appropriateness |      15% |
| **Total**             | **100%** |

Formula:

```text

German Score =

   Grammar × 0.25

 + Vocabulary × 0.20

 + Sentence Structure × 0.20

 + Naturalness × 0.20

 + Level Appropriateness × 0.15

```

---

# 15. German Dimension: Grammar

Evaluate:

- verb position

- articles

- cases

- adjective endings

- prepositions

- verb conjugation

- tense

- modal constructions

- subordinate clauses

- relative clauses

- conditional structures

- conjunctions

The evaluator should consider the target level.

A grammatical structure that is acceptable for B2 may be insufficient for a C1 learner when more sophisticated structures are reasonably expected.

---

# 16. German Dimension: Vocabulary

Evaluate:

- correctness

- range

- precision

- word choice

- collocations

- topic-specific vocabulary

- repetition

- ability to express nuanced ideas

Example:

Basic:

> Das ist ein großes Problem.

More precise:

> Das könnte langfristig erhebliche wirtschaftliche Folgen haben.

The second demonstrates stronger lexical precision.

---

# 17. German Dimension: Sentence Structure

Evaluate:

- sentence construction

- clause relationships

- word order

- complexity

- cohesion

- use of subordinate clauses

- logical connection between sentences

The goal is not to reward unnecessarily complicated sentences.

Complexity should support communication.

---

# 18. German Dimension: Naturalness

Naturalness measures whether the German sounds like something a proficient German speaker would naturally express.

A sentence may be grammatically understandable but unnatural.

Example:

> Das macht einen großen Einfluss auf die Gesellschaft.

Understandable, but unnatural.

More natural:

> Das hat einen großen Einfluss auf die Gesellschaft.

Naturalness should therefore be evaluated separately from grammatical correctness.

---

# 19. German Dimension: Level Appropriateness

The evaluator must consider the learner's target level.

Supported initial levels:

```text

B2

C1

```

The evaluator should consider whether the response demonstrates language appropriate for that level.

### B2

Expected characteristics include:

- clear argumentation

- reasonably varied vocabulary

- connected discourse

- explanation of opinions

- appropriate subordinate clauses

- ability to discuss abstract topics

### C1

Expected characteristics include:

- flexible expression

- precise vocabulary

- nuanced argumentation

- sophisticated sentence structures

- strong cohesion

- ability to express qualifications and distinctions

- natural handling of abstract and complex subjects

C1 evaluation should not simply penalize a learner for using simple sentences.

The evaluator should assess whether the response provides evidence of C1-level control where the task reasonably allows it.

---

# 20. Evidence

Evidence is a first-class evaluation output.

A score without evidence is insufficient.

Every important evaluation should answer:

> Why did the learner receive this score?

Conceptual model:

```python

class Evidence(BaseModel):

   dimension: str

   observation: str

   impact: str

```

Example:

```json
{
  "dimension": "reasoning",

  "observation": "The learner connects unchecked AI output with incorrect business decisions.",

  "impact": "This demonstrates a clear causal relationship."
}
```

---

# 21. Thinking Evidence

Thinking evidence should reference actual characteristics of the learner's response.

Examples:

### Positive

> Identified a concrete financial risk and explained how it could result from incorrect AI recommendations.

### Negative

> Mentions that AI is risky but does not explain what could go wrong or why.

### Hat adherence

> The response focuses on negative consequences and remains within the Black Hat perspective.

### Contamination

> The learner moves from identifying a risk to proposing a solution, which weakens Black Hat adherence.

Evidence should be specific rather than generic.

Bad:

> Good reasoning.

Better:

> You explained the connection between employee dependence on AI and the risk of reduced independent decision-making.

---

# 22. German Evidence

German evidence should reference actual language behavior.

Examples:

### Grammar

> The subordinate clause correctly places the finite verb at the end.

### Vocabulary

> "erhebliche Auswirkungen" is precise and appropriate for a C1 discussion.

### Naturalness

> "eine Entscheidung treffen" is more natural here than "eine Entscheidung machen."

### Weakness

> The sentence is understandable, but the preposition used with this verb is incorrect.

Evidence should explain the improvement.

---

# 23. Corrections

Corrections should be selective.

The evaluator should not rewrite every sentence.

A correction should normally contain:

```python

class Correction(BaseModel):

   original: str

   corrected: str

   explanation: str

   category: str

```

Example:

```json
{
  "original": "Das macht einen großen Einfluss.",

  "corrected": "Das hat einen großen Einfluss.",

  "explanation": "The natural collocation is 'Einfluss haben'.",

  "category": "naturalness"
}
```

Prioritize:

1. repeated mistakes

2. meaningful mistakes

3. mistakes relevant to B2/C1 development

4. errors that affect clarity

5. high-value naturalness improvements

---

# 24. Score Anchors

Numeric scores should have stable interpretations.

## Thinking

|  Score | Meaning                           |
| -----: | --------------------------------- |
| 90–100 | Exceptional thinking for the task |
|  80–89 | Strong                            |
|  70–79 | Good                              |
|  60–69 | Adequate                          |
|  50–59 | Weak                              |
|  30–49 | Very weak                         |
|   0–29 | Insufficient                      |

## German

|  Score | Meaning                                |
| -----: | -------------------------------------- |
| 90–100 | Excellent command for the target level |
|  80–89 | Strong                                 |
|  70–79 | Good                                   |
|  60–69 | Adequate                               |
|  50–59 | Weak                                   |
|  30–49 | Very weak                              |
|   0–29 | Insufficient                           |

These anchors should be validated against the evaluation harness.

---

# 25. Score Calibration

Scores must not be interpreted as absolute measurements of language proficiency or intelligence.

A score represents performance on the current LinguaMentis task.

For example:

```text

German Score: 82

```

means:

> Strong German performance in this response according to the LinguaMentis rubric.

It does not mean:

> The learner has an objectively measured C1 proficiency of 82%.

---

# 26. Handling Short Responses

Short does not automatically mean bad.

Evaluation should distinguish:

```text

Short + precise + well-reasoned

```

from:

```text

Short + unsupported + shallow

```

Example:

> Das größte Risiko besteht darin, dass Unternehmen falsche KI-Ergebnisse ungeprüft übernehmen.

This is short but specific.

The evaluator should not penalize it merely because it is short.

---

# 27. Handling Long Responses

Longer responses do not automatically deserve higher scores.

The evaluator should not reward:

- repetition

- unnecessary explanations

- verbosity

- irrelevant details

The goal is **quality of thinking**, not quantity of text.

---

# 28. Handling Mixed-Hat Responses

A response may contain multiple thinking modes.

The evaluator should identify whether the additional mode:

1. supports the current Hat, or

2. represents contamination.

Example:

Black Hat:

> Ein Risiko besteht darin, dass KI falsche Empfehlungen gibt. Deshalb sollte das Unternehmen die Ergebnisse überprüfen.

The first sentence is Black Hat.

The second introduces a solution.

Evaluation:

```text

Risk identification: strong

Hat adherence: reduced

```

The evaluator should not mark the entire response as invalid.

---

# 29. Thinking vs German Interaction

The evaluator must avoid allowing language errors to distort thinking scores.

Example:

> KI könnte viele fehlerhafte Entscheidung machen, weil Mitarbeiter die Resultate nicht kontrollieren.

German:

- grammar error

- vocabulary/form error

Thinking:

- clear risk

- causal relationship

- relevant consequence

Therefore:

```text

Thinking Quality → potentially high



German Quality → reduced

```

This separation is mandatory.

---

# 30. Recommendations

Recommendations should be actionable.

Weak:

> Improve your German.

Better:

> Practice causal connectors such as "dadurch", "deshalb", "wodurch" and "infolgedessen" to express consequences more precisely.

Thinking recommendation:

> When identifying a risk, continue one step further and explain the consequence that could result from it.

Recommendations should focus on the learner's demonstrated weaknesses.

---

# 31. Evaluation Response Structure

A complete evaluation should conceptually follow:

```text

Evaluation
│
├── Thinking
│   ├── Score
│   ├── Dimensions
│   ├── Evidence
│   ├── Strengths
│   ├── Weaknesses
│   └── Recommendations
│
└── German
   ├── Score
   ├── Dimensions
   ├── Evidence
   ├── Corrections
   ├── Strengths
   ├── Weaknesses
   └── Recommendations

```

---

# 32. Evaluation Ordering

User-facing feedback should normally appear in this order:

```text

1. Thinking

2. German

3. Next challenge

```

This reflects the product philosophy:

> Thinking first. Language second.

Example:

> **Thinking:** You identified a genuine risk and explained its consequence. However, your final sentence proposes a solution, so the response partially leaves the Black Hat perspective.

> **German:** Your argument is clear. "Dadurch könnten langfristig höhere Kosten entstehen" would sound more natural than the current formulation.

> **Next challenge:** Bleibe beim Black Hat. Welche weitere indirekte Folge könnte entstehen?

---

# 33. Evaluation Reliability

LLM evaluation is probabilistic.

Therefore LinguaMentis should not assume that one evaluator response is always correct.

The system should eventually measure:

- evaluator consistency

- score variance

- agreement with reference evaluations

- false positives

- false negatives

- model-to-model differences

- prompt-to-prompt differences

- regression after prompt changes

This becomes the responsibility of the evaluation harness.

---

# 34. Evaluation Harness

The rubric is designed to become executable as a test specification.

Conceptual structure:

```text

evaluation/
├── datasets/
│   ├── thinking/
│   └── german/
│
├── cases/
├── runners/
├── metrics/
└── reports/

```

A test case may contain:

```json
{
  "id": "black-001",

  "level": "B2",

  "hat": "BLACK",

  "topic": "AI in the workplace",

  "response": "...",

  "expected": {
    "hat_adherence": "high",

    "reasoning": "medium",

    "depth": "medium"
  }
}
```

The harness can then test:

```text

Case
↓
Evaluator
↓
Structured Evaluation
↓
Expected Evaluation
↓
Metrics
↓
Regression Report

```

---

# 35. Evaluator Independence

The evaluation system must remain independent from the Hat Agent.

```text

BlackHatAgent

   ↓

generates challenge



Learner
   ↓
responds


ThinkingEvaluator
   ↓
evaluates response


GermanEvaluator
   ↓
evaluates language

```

The Black Hat Agent should not determine its own score.

This reduces self-confirming behavior and makes the system easier to test.

---

# 36. Learning History

Evaluation results become part of the learner's journey.

For each evaluated response, LinguaMentis should preserve:

- thinking score

- German score

- dimension scores

- evidence

- corrections

- strengths

- weaknesses

- recommendations

- Hat

- target level

- MindQuest

- Turn

This allows future analysis such as:

```text

Black Hat

Thinking: 61 → 68 → 74 → 81



German:

B2: 72 → 76 → 79 → 83

```

The system can therefore identify actual development rather than only showing the latest score.

---

# 37. Learning Profile

`UserLearningProfile` is derived from accumulated evaluation data.

It should not be treated as the primary source of truth.

Conceptually:

```text

MindQuest
  ↓
Turns
  ↓
Evaluations
  ↓
Evidence
  ↓
Historical Analysis
  ↓
UserLearningProfile

```

The profile may eventually identify:

### Thinking

- strongest Hat

- weakest Hat

- strongest reasoning dimension

- weakest reasoning dimension

- improvement trend

### German

- grammar patterns

- vocabulary weaknesses

- naturalness issues

- recurring corrections

- B2/C1 progression

---

# 38. Important Evaluation Rules

### Rule 1

Never combine Thinking Score and German Score into one score.

### Rule 2

Do not use German mistakes as evidence of poor thinking.

### Rule 3

Do not use sophisticated German as evidence of sophisticated thinking.

### Rule 4

Evaluate Hat adherence explicitly.

### Rule 5

Provide evidence for meaningful scores.

### Rule 6

Do not reward verbosity automatically.

### Rule 7

Do not penalize concise but high-quality reasoning.

### Rule 8

Evaluate language according to the learner's target level.

### Rule 9

Corrections should be selective and useful.

### Rule 10

The evaluator must remain independent from the Hat Agent.

---

# 39. Example Complete Evaluation

## Learner Response

> KI kann in Unternehmen ein Risiko sein, weil Mitarbeiter falsche Informationen übernehmen könnten. Dadurch könnten sie falsche Entscheidungen treffen. Deshalb sollte man die KI immer kontrollieren.

## Active Hat

Black

## Thinking Evaluation

**Score: 78**

| Dimension     | Score |
| ------------- | ----: |
| Hat Adherence |    82 |
| Relevance     |    90 |
| Reasoning     |    78 |
| Depth         |    68 |
| Specificity   |    74 |

### Evidence

- Identifies a concrete risk involving incorrect AI-generated information.

- Explains a causal chain from incorrect information to incorrect decisions.

- The final sentence introduces a solution, which slightly reduces Black Hat adherence.

- The response explores one consequence but does not examine a deeper second-order consequence.

### Strengths

- Clear risk identification.

- Relevant causal reasoning.

- Concrete consequence.

### Weaknesses

- Limited depth.

- Moves into solution generation.

### Recommendation

> Stay with the consequence for one more step before proposing a solution. Ask what could happen if incorrect decisions affect customers, finances, or employees.

---

## German Evaluation

**Score: 81**

| Dimension             | Score |
| --------------------- | ----: |
| Grammar               |    88 |
| Vocabulary            |    76 |
| Sentence Structure    |    82 |
| Naturalness           |    82 |
| Level Appropriateness |    78 |

### Evidence

- The causal structure using "weil" and "dadurch" is clear.

- Vocabulary is accurate but relatively general for a C1-level discussion.

- The sentence structure is clear and appropriately connected.

- "falsche Informationen übernehmen" is understandable and contextually appropriate.

### Recommendation

> For C1, try more precise expressions such as "fehlerhafte Informationen übernehmen", "auf fehlerhaften Ergebnissen beruhen" or "Fehlentscheidungen verursachen".

---

# 40. Future Extensions

The initial rubric focuses on:

```text

Thinking Quality

German Quality

```

Future versions may add independent dimensions such as:

- speaking fluency

- pronunciation

- pacing

- pauses

- intonation

- interaction quality

- vocabulary growth

- long-term reasoning improvement

These should remain separate dimensions rather than being mixed into the existing scores.

---

# 41. Final Principle

The purpose of evaluation in LinguaMentis is not to tell the learner:

> "Your answer is good."

It is to help the learner understand:

> **How did I think?**

> **How well did I express that thinking in German?**

> **What evidence supports that evaluation?**

> **What should I improve next?**

Therefore:

```text

Response

  ↓

Understand the thinking

  ↓

Evaluate the thinking

  ↓

Understand the German

  ↓

Evaluate the German

  ↓

Provide evidence

  ↓

Provide actionable feedback

  ↓

Challenge the learner again

```

**The evaluation is not the end of the learning loop.**

It is the mechanism that makes the next thinking step better.
