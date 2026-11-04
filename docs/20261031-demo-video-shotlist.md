# Demo video shot list — Own Words

**Hard limit:** under 3 minutes. Target 2:30, which leaves room to breathe.
**Format:** screen recording of the terminal, voice-over. No slides, no face cam needed.
**Setup:** terminal at ~100 columns, large font, dark background. Run with
`COACH_MODEL_ID=us.anthropic.claude-sonnet-5-5` and `AWS_REGION=us-east-1`.

Record the session **live** rather than splicing takes — the agent's output is
non-deterministic, and a visibly real run is more persuasive than a clean one.
Each agent call takes a few seconds; a full three-question session took about
40 seconds of model time in rehearsal. Speeding up the waits in the edit is fine;
cutting or reordering output is not.

The scores below are **not scripted** — read whatever is on screen. Narration
lines in `[brackets]` are placeholders for the live number.

---

## 0:00 – 0:20 · The problem (talk over a blank or title terminal)

> "A nurse with eight years on the ward loses a job to someone with two — because
> in the interview she said 'patient was very angry, I called doctor' instead of
> 'the patient escalated, so I paged the attending.' Same facts. Same competence.
> Different polish. Coaching that fixes this costs $150 an hour."

Keep this under 20 seconds. The problem is the hook; don't linger.

## 0:20 – 0:35 · Launch

Show the command being typed and run. Narrate while the setup prompts appear:

> "Three Strands agents on Bedrock — an interviewer, an evaluator, a coach.
> I'll answer as a support rep whose first language is Hindi."

Type the setup answers live: `Customer support representative` / `Entry level` / `Hindi`.

## 0:35 – 1:05 · Q1: the weak answer and the two scores

Paste the deliberately weak, mixed-language first answer:

```text
customer bahut gussa tha about late delivery, I said sorry and gave him refund, he was okay after
```

When the feedback panel appears, **pause on it**:

> "Two scores, not one. Content [N]. English [N]. That separation is the whole
> point — it tells her which problem she actually has. And the evidence is quoted
> from her own words, so the critique isn't generic. The coaching is in Hindi,
> with an English back-translation so anyone can check it."

## 1:05 – 1:25 · Q1: the honesty constraint

Scroll to the "answer you could have given" panel and point at the brackets:

> "It rebuilt her answer using only the facts she gave. It doesn't know how late
> the delivery was, so it asks. My first version invented 'four days late' —
> that's a detail she'd memorize and get caught on in a real interview."

This beat is the originality argument. Don't rush it.

## 1:25 – 1:45 · Q1: the retry, and the proof

Paste the stronger English retry:

```text
A customer called because his order was four days late and he was very angry. I listened to his full complaint without interrupting, apologized, and checked the tracking myself. I gave him a full refund on the shipping and a discount code, and I called him back the next day to confirm the parcel arrived. He thanked me and kept ordering from us.
```

When the before/after line appears:

> "Same question. Not a new one. The only thing that changed in between was the
> coaching — so the difference is attributable to it. Content [N] to [N]."

## 1:45 – 2:10 · Q2: answering in Hindi (speed up the waits)

Paste a first answer that is mostly Hindi:

```text
jab bahut saare customer wait kar rahe hote hain, toh main pehle wo dekhta hoon jiska problem sabse serious hai.
```

When the feedback panel shows `English —   not in English, so not scored`:

> "This time she answers in Hindi. The tool invited her to, so it doesn't score
> that as failed English — it shows a dash. Content is still scored, because the
> substance is there in any language."

Then paste the English retry and let it score — no narration needed:

```text
When many customers are waiting, I first help the person whose problem is most serious, because their service is blocked. Then I answer the simple questions quickly, and I tell the others how long they will wait.
```

## 2:10 – 2:20 · Q3 (fast-forward, no narration)

```text
i dont know the answer i ask my senior
```

```text
If I do not know the answer, I tell the customer honestly that I will check and call back. Then I ask my senior, and I call the customer back with the correct answer.
```

## 2:20 – 2:30 · The report

Let the session report table render. Point at the Q2 row's English dash:

> "Content up on every question, on identical questions. And where she answered
> in Hindi, English shows a dash, not a zero."

Answer `n` to the save prompt on camera — it's the privacy beat for free.

## 2:30 – 2:45 · Close

> "Runs locally against your own Bedrock account. No server, nothing uploaded,
> nothing saved unless you say yes. Source is on GitHub — own-words."

---

## Pre-flight checklist

- [ ] Clear scrollback (`clear`) before recording
- [ ] Hide any AWS account IDs / SSO profile names visible in the prompt
- [ ] `export AWS_PROFILE=... COACH_MODEL_ID=... AWS_REGION=...` beforehand so it isn't in frame
- [ ] Have all six answers in a scratch file to paste — typing them burns 40 seconds
- [ ] Do one throwaway run first to warm up and check scores land sensibly
- [ ] Confirm total runtime under 3:00 before uploading
- [ ] Upload as **public** (or unlisted, if the rules allow it) and paste the link into the article

## If the live run scores badly

The agent is non-deterministic and occasionally gives a retry a flat or lower
score, or judges the mixed Q1 answer as "not in English". Do not re-record until
you get a flattering number — if it happens, keep it and say so: "it didn't
improve that one, and the tool says so rather than flattering me." That is a
stronger claim about the tool than a good score is.
