# Demo video shot list — Own Words

**Hard limit:** under 3 minutes. Target 2:30, which leaves room to breathe.
**Format:** screen recording of the terminal, voice-over. No slides, no face cam needed.
**Setup:** terminal at ~100 columns, large font, dark background. Run with
`COACH_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0`.

Record the session **live** rather than splicing takes — the agent's output is
non-deterministic, and a visibly real run is more persuasive than a clean one.

---

## 0:00 – 0:25 · The problem (talk over a blank or title terminal)

> "A nurse with eight years on the ward loses a job to someone with two — because
> in the interview she said 'patient was very angry, I called doctor' instead of
> 'the patient escalated, so I paged the attending.' Same facts. Same competence.
> Different polish. Coaching that fixes this costs $150 an hour."

Keep this under 25 seconds. The problem is the hook; don't linger.

## 0:25 – 0:40 · Launch

Show the command being typed and run. Narrate while the setup prompts appear:

> "Three Strands agents on Bedrock — an interviewer, an evaluator, a coach.
> I'll answer as a support rep whose first language is Hindi."

Type the setup answers live: `Customer support representative` / `Entry level` / `Hindi`.

## 0:40 – 1:10 · The weak answer and the two scores

Paste the deliberately weak first answer:

```
customer bahut gussa tha about late delivery, I said sorry and gave him refund, he was okay after
```

When the feedback panel appears, **pause on it** and say the key line:

> "Two scores, not one. Content four. English five. That separation is the whole
> point — it tells her which problem she actually has. And the evidence is quoted
> from her own words, so the critique isn't generic."

## 1:10 – 1:35 · The honesty constraint

Scroll to the "answer you could have given" panel and point at the brackets:

> "It rebuilt her answer using only the facts she gave. It does not know how many
> days late the delivery was, so it asks. My first version invented 'four days late'
> — that's a detail she'd memorise and get caught on in a real interview."

This beat is the originality argument. Don't rush it.

## 1:35 – 2:05 · The retry, and the proof

Paste the stronger English retry. When the before/after line appears:

> "Same question. Not a new one. The only thing that changed in between was the
> coaching — so the difference is attributable to it. Content four to seven."

## 2:05 – 2:25 · The report

Let the session report table render.

> "Across the session, content up four points on average. And where she answered
> in Hindi, English shows a dash — not a zero. The tool invited her to use her own
> language; scoring that as failed English would punish her for accepting."

## 2:25 – 2:40 · Close

> "Runs locally against your own Bedrock account. No server, nothing uploaded,
> nothing saved unless you say yes. Source is on GitHub — own-words."

---

## Pre-flight checklist

- [ ] Clear scrollback (`clear`) before recording
- [ ] Hide any AWS account IDs / SSO profile names visible in the prompt
- [ ] `export COACH_MODEL_ID=...` beforehand so it isn't in frame
- [ ] Have both answers in a scratch file to paste — typing them burns 40 seconds
- [ ] Do one throwaway run first to warm up and check scores land sensibly
- [ ] Confirm total runtime under 3:00 before uploading

## If the live run scores badly

The agent is non-deterministic and occasionally gives a retry a flat or lower
score. Do not re-record until you get a flattering number — if it happens, keep
it and say so: "it didn't improve that one, and the tool says so rather than
flattering me." That is a stronger claim about the tool than a good score is.
