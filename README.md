# Own Words

**An interview coach that never puts words in your mouth.**

A mock interview coach for people who lose jobs they could do because of how they
*sound* in an interview, not what they can do.

Non-native English speakers, refugees and first-generation job seekers are routinely
filtered out for interview polish — phrasing, structure, confidence — while candidates
with weaker substance advance. Professional coaching costs $100–200 an hour and is
effectively out of reach for exactly the people who would benefit most.

This agent does two things a general-purpose chatbot does not:

1. **It separates "your answer was weak" from "your English was weak."** Two scores,
   side by side, and the coaching is written in the language you think in. If your
   content is strong and your English is holding you back, you can see that — and the
   reverse.
2. **It proves you got better.** After the coaching, you answer *the same question
   again* and it is scored again. The before and after are on identical input, so the
   improvement is attributable to the coaching rather than to an easier question.

Answer the first time in whatever language is easiest — English, your own, or a mix.
The retry is the rehearsal, so it asks you for English. If an answer is not in
English, the English axis reports `—` rather than a low score: you were invited to
answer in your own language, and scoring that as failed English would punish you for
accepting the invitation. Content is still scored either way, because the substance
is there to judge whatever language it arrives in.

It will never put words in your mouth. The model answer it builds is assembled only
from facts you actually gave it; anything a strong answer would need but you did not
supply appears as a bracketed prompt — `[how many days late?]` — for you to fill in.
That matters because a detail invented on your behalf is one you might memorise and
repeat in a real interview.

## What a session looks like

```
╭─ Question 1 of 3 ───────────────────────────────────────────────────────╮
│ Tell me about a time a customer was angry with you. What did you do?    │
╰─────────────────────────────────────────────────────────────────────────╯

Your answer: customer bahut gussa tha about late delivery, I said sorry
             and gave him refund, he was okay after

╭─ Feedback ──────────────────────────────────────────────────────────────╮
│ Content 4/10   structure 2 · specificity 3 · ownership 6                │
│ English 5/10                                                            │
╰─────────────────────────────────────────────────────────────────────────╯
आपका उत्तर सही दिशा में है लेकिन बहुत छोटा है...
⤷ (en) Your answer is in the right direction but very short...

╭─ The answer you could have given ───────────────────────────────────────╮
│ A customer was very upset because of a late delivery [how many days     │
│ late?]. I apologised and told him [what exactly did you say?]...        │
│ ⤷ anything in [brackets] is yours to fill in — it was not invented      │
╰─────────────────────────────────────────────────────────────────────────╯

Now try that same question again, in English this time - the real interview
will be in English, so this is the rehearsal
  Tell me about a time a customer was angry with you. What did you do?
Your answer: A customer called because his order was four days late. I
             listened to his full complaint without interrupting, then...

Content 4 → 7   English not scored   ✦ you improved this answer
  one of these answers was not in English, so there was no English to compare
```

## Prerequisites

This is not a five-minute setup unless you already have Bedrock working. You need:

- Python 3.11 or newer
- An AWS account with **Amazon Bedrock model access granted** for an Anthropic model
  (request it in the Bedrock console; approval is not instant on a new account)
- AWS credentials configured locally (`aws configure`, SSO, or environment variables)

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Find your model ID

Model availability differs by account and region, so the model ID is not hardcoded.
List what your account can actually invoke:

```bash
aws bedrock list-inference-profiles --region us-east-1 \
  --query 'inferenceProfileSummaries[?contains(inferenceProfileId, `anthropic`)].inferenceProfileId' \
  --output text
```

## Run

```bash
export COACH_MODEL_ID=us.anthropic.claude-sonnet-5   # one from the list above
export AWS_REGION=us-east-1
.venv/bin/python -m coach
```

## How it is built

Three specialist agents, each built with the [Strands Agents SDK](https://github.com/strands-agents/sdk-python):

| Agent | Job | Hard constraint |
|---|---|---|
| Interviewer | Asks one role-specific question at a time | Never repeats a theme; holds difficulty flat so scores stay comparable across the session |
| Evaluator | Scores structure, specificity, ownership and English 0–10 | Must quote the candidate's own words as evidence; never blends content with English; declines to score English at all on an answer that was not written in English |
| Coach | Explains the score in the candidate's first language | Model answer uses only facts the candidate supplied; gaps become bracketed prompts |

They are driven by a **deterministic Python loop**, not an orchestrator agent or a
swarm. That is a deliberate choice: the sequence is fixed (ask → score → coach →
retry → re-score), and an orchestrator that decided to skip the evaluator would break
the one number this tool exists to produce. The intelligence belongs inside each
agent; the control flow does not need any.

Each call gets a **fresh agent**. A reused evaluator would carry conversation history
and score the retry while remembering the first attempt — exactly the anchoring that
would inflate the improvement figure.

## Languages

Demonstrated in **English and Hindi**. The prompts are language-agnostic and should
work for others, but nothing else has been tested, so nothing else is claimed. The
coach always prints an English back-translation beside its first-language feedback,
so the quality of a translation can be checked by someone who does not read that
language.

## Privacy

There is no account, no server, and nothing is uploaded anywhere we run. Your answers
go to Amazon Bedrock in your own AWS account and nowhere else. The session is saved to
a local JSON file **only if you say yes** when asked at the end — interview answers
can touch immigration status, health or workplace mistreatment, so nothing is written
to disk by default. `session*.json` is gitignored.

## Tests

```bash
.venv/bin/pip install pytest
.venv/bin/pytest
```

No test makes a network call. The session loop takes its three agents as injected
callables, so the whole flow is exercised with fakes and costs nothing to run.

## Built for

The [AWS "Strands SDK: Workshop to Ship" hackathon](https://builder.aws.com/), social
good / education track.
