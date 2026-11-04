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
That matters because a detail invented on your behalf is one you might memorize and
repeat in a real interview.

## What a session looks like

```
╭─ Question 1 of 3 ───────────────────────────────────────────────────────╮
│ Tell me about a time you helped someone who was upset or frustrated.    │
│ What did you do, and how did the situation end?                         │
╰─────────────────────────────────────────────────────────────────────────╯
Your answer: ek customer bahut gussa tha kyunki uski delivery late thi.
             maine unki poori baat suni, sorry bola aur refund de diya.
             baad mein woh theek ho gaye.

╭─ Feedback ──────────────────────────────────────────────────────────────╮
│ Content 4/10   structure 4 · specificity 2 · ownership 7                │
│ English —   not in English, so not scored                               │
│   “ek customer bahut gussa tha kyunki uski delivery late thi”           │
│   “maine unki poori baat suni, sorry bola aur refund de diya”           │
│   “baad mein woh theek ho gaye”                                         │
╰─────────────────────────────────────────────────────────────────────────╯
आपका जवाब सीधा और साफ़ है, और आपने खुद कदम उठाए: ध्यान से सुनना, माफ़ी
माँगना और रिफंड देना। कमी यह है कि ठोस details नहीं हैं...
⤷ (en) Your answer is direct and clear, and you took the actions yourself:
listening carefully, apologizing and giving a refund. What's missing is
concrete details, such as how late the delivery was...

╭─ The answer you could have given ───────────────────────────────────────╮
│ A customer was very angry because their delivery was late [how many     │
│ days late? what was the order?]. I listened to their whole complaint    │
│ without interrupting [what did they say they were most upset about?].   │
│ I apologized and gave them a refund [full or partial? how did you       │
│ decide to offer it?]. After that, the customer was fine [how did you    │
│ know? what did they say or do? did they order again?].                  │
│ ⤷ anything in [brackets] is yours to fill in — it was not invented for  │
│ you                                                                     │
╰─────────────────────────────────────────────────────────────────────────╯
Now try that same question again, in English this time - the real interview
will be in English, so this is the rehearsal
Your answer: A customer was angry because his delivery was late. I listened
             to his whole complaint without interrupting, said sorry, and
             gave him a refund. After that he calmed down and thanked me.

Content 4 → 6   English not scored        ✦ you improved this answer
  one of these answers was not in English, so there was no English to compare
```

Excerpted from a real run on Amazon Bedrock (`us.anthropic.claude-sonnet-5-5`):
rewrapped to fit, the Hindi feedback shortened, and the model's spelling normalized
to US English. The output is non-deterministic, so your scores and wording will
differ.

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

This needs AWS CLI v2; older v1 builds do not have `list-inference-profiles`.

## Run

```bash
export AWS_PROFILE=your-profile                       # if you use named profiles or SSO
export COACH_MODEL_ID=us.anthropic.claude-sonnet-5-5  # or another ID from the list above
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

## License

MIT — see [LICENSE](LICENSE).
