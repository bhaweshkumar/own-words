# Own Words: an interview coach that never puts words in your mouth

**Focus area:** Education · **Built with:** Strands Agents SDK on Amazon Bedrock · **Repo:** https://github.com/bhaweshkumar/own-words

---

## The problem is not that they can't do the job

A nurse with eight years of ward experience loses a job to someone with two, because in the interview she said "patient was very angry, I called doctor" instead of "the patient escalated, so I paged the attending and stayed with the family until he arrived."

Same facts. Same competence. Different polish.

This happens at scale. Non-native English speakers, refugees, and first-generation job seekers are routinely filtered out of hiring processes for how an answer *sounds*, while candidates with weaker substance advance. The fix that exists — interview coaching — runs $100 to $200 an hour, which prices out precisely the people it would help most.

So the gap is not skill. It is rehearsal. Nobody is sitting across from these candidates asking a hard question, listening to the answer, and telling them exactly what was missing.

## What Own Words does differently

A general-purpose chatbot will happily critique your interview answer. Two things make this agent not that.

### 1. It separates "your answer was weak" from "your English was weak"

Every answer gets two independent scores: **content** (structure, specificity, ownership) and **English** (grammar, word choice, fluency). They are never blended into one number, because blending them destroys the only diagnostic that matters.

If your content scores 8 and your English scores 4, your problem is language, and the fix is practice and phrasing. If content is 3 and English is 9, you are articulate and saying nothing, and the fix is completely different. One combined "6/10" tells you to try harder at an unspecified thing.

The coaching itself is written in the candidate's first language, with an English back-translation printed beside it — so a coach, a teacher, or a friend who doesn't read that language can still check what the agent said.

### 2. It proves you got better, on the same question

This is the part I had to redesign.

My first version asked five different questions and showed a rising score. A reviewer pointed out the obvious: nothing in that design *causes* the improvement. Different questions have different difficulty. A nice-looking upward curve would have been authored by me, not earned by the user.

So every question now runs a **coached retry**:

```
ask → score → coach → answer the SAME question again → re-score
```

Before and after are measured on identical input. Whatever the difference is, the coaching in between is the only thing that changed.

```
╭─ Question 1 of 3 ───────────────────────────────────────────────────────╮
│ Tell me about a time a customer was angry with you. What did you do?    │
╰─────────────────────────────────────────────────────────────────────────╯

Your answer: customer bahut gussa tha about late delivery, I said sorry
             and gave him refund, he was okay after

╭─ Feedback ──────────────────────────────────────────────────────────────╮
│ Content 4/10   structure 2 · specificity 3 · ownership 6                │
│ English 5/10                                                            │
│   "customer bahut gussa tha"                                            │
│   "I said sorry"                                                        │
╰─────────────────────────────────────────────────────────────────────────╯
आपका उत्तर सही दिशा में है लेकिन बहुत छोटा है...
⤷ (en) Your answer is in the right direction but very short...

Now try that same question again, in English this time — the real
interview will be in English, so this is the rehearsal

Content 4 → 7   English 5 → 9      ✦ you improved this answer
```

Across the live sessions I've run against Bedrock, coached retries average **+4 on content** and **+2.5 on English**, on identical questions. That number is small, honest, and reproducible — you can run it yourself and get your own.

## It will not invent your experience

The agent builds a "the answer you could have given" for every question. The hard rule: **it may only use facts the candidate actually supplied.**

Where a strong answer needs a specific the candidate didn't give, the agent writes a bracketed prompt instead of a plausible detail:

```
╭─ The answer you could have given ───────────────────────────────────────╮
│ A customer was very upset because of a late delivery [how many days     │
│ late?]. I apologised and told him [what exactly did you say?]...        │
│ ⤷ anything in [brackets] is yours to fill in — it was not invented      │
╰─────────────────────────────────────────────────────────────────────────╯
```

My own first draft of this prompt produced a model answer containing "four days late" and "I checked the tracking record." The candidate had said neither. For this audience that is not a harmless flourish — it is a detail someone memorises, repeats in a real interview, and gets caught on. A model answer that is almost entirely brackets is a *correct* result, not a failure.

## The architecture, and the part that is deliberately boring

Three specialist Strands agents:

| Agent | Job | Hard constraint |
|---|---|---|
| **Interviewer** | Asks one role-specific question at a time | Never repeats a theme; holds difficulty **flat** across the session, so scores stay comparable |
| **Evaluator** | Scores structure, specificity, ownership, English | Must quote the candidate's own words as evidence; never blends the two axes |
| **Coach** | Explains the score in the candidate's first language | Model answer uses only supplied facts; gaps become bracketed prompts |

Each is a `strands.Agent` over a shared `BedrockModel`, using `agent.structured_output(PydanticModel, prompt)` so scores come back as validated types rather than prose I have to parse.

The workshop this hackathon is built around ends at multi-agent swarms, so the obvious move was to put an orchestrator agent on top. **I deliberately didn't.**

The sequence here is fixed — ask, score, coach, retry, re-score — and it is the *measurement apparatus*. An orchestrator that decided to skip the evaluator, or coach twice, or reorder a step, would quietly corrupt the one number this tool exists to produce. So the control flow is a plain Python loop with the three agents injected as callables. The intelligence lives inside each agent; the loop does not need any.

That choice paid for itself twice:

- **Every test runs offline.** The loop takes its agents as injected callables, so all 65 tests use fakes. No test makes a network call, nothing costs money to run, and the whole suite finishes in under half a second.
- **The before/after is anchoring-proof.** Each call builds a *fresh* agent. A reused evaluator would carry conversation history and score the retry while remembering the first attempt — which is exactly the contamination that would inflate the improvement figure. There's a test asserting two separate agent constructions per round, because the entire claim rests on it.

## Three things that only showed up live

**The SDK was printing over my interface.** Strands agents stream to stdout by default. Every question appeared twice and `Tool #1: Evaluation` leaked into the panels. `callback_handler=None` fixes it — and now every agent in the module is built through one factory function so nobody can quietly reintroduce it.

**An undescribed schema field is a field the model skips.** My `Evaluation` model had `english: int` with no `description`. The model, handed a JSON schema containing an unexplained integer, simply omitted it — and the session died on a validation error. Every LLM-filled field now carries a description explaining what it is *and why it matters*. Those descriptions are prompt surface, not documentation.

**The evaluator was punishing people for accepting an invitation.** This one is my favourite, because the bug was in my ethics rather than my code. The tool tells users to answer in whatever language is easiest. So a user answered in romanised Hindi — and the evaluator, correctly observing there was almost no English present, scored English 0. The session report then proudly announced `english -3.0`.

The scorer wasn't wrong. The *question* was wrong. "How good is the English in this answer?" is meaningless when the answer isn't in English, and the resulting zero reads as a failure rather than as a language choice the tool itself encouraged.

The evaluator now reports `answered_in_english` alongside the score. When an answer isn't in English, the English axis reports `—` and is dropped from the average and from the advice — while content is still scored in full, because the substance is there to judge whatever language it arrives in. The retry prompt now also asks for English explicitly, since the retry is the rehearsal and the real interview will be in English.

A tool for people who are judged unfairly on language cannot itself judge them unfairly on language.

## Privacy, because of who this is for

No account, no server, no telemetry. Answers go to Amazon Bedrock in the user's own AWS account and nowhere else. The session is written to disk **only** if the user says yes when asked at the end — interview answers touch immigration status, health, and workplace mistreatment, so nothing is persisted by default.

## Try it

```bash
git clone https://github.com/bhaweshkumar/own-words && cd own-words
python3 -m venv .venv && .venv/bin/pip install -e .

export COACH_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
export AWS_REGION=us-east-1
.venv/bin/python -m coach
```

Demonstrated in English and Hindi. The prompts are language-agnostic and should work for others — but nothing else has been tested, so nothing else is claimed.

---

*Built for the AWS "Strands SDK: Workshop to Ship" hackathon, education and social good track.*
