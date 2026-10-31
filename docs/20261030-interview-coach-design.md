# First Language Interview Coach — Design

**Date:** 2026-10-30
**Status:** Proposed — awaiting approval
**Hackathon:** Strands SDK: Workshop to Ship (submissions close 2026-11-04, 11:59 PM PST)
**Focus area:** Education
**Source requirements:** [requirements.txt](requirements.txt)

---

## 1. Intent and why

Millions of capable people lose jobs they could do because of how they *sound* in an
interview, not what they can do. Non-native English speakers, refugees, and
first-generation job seekers are filtered out for interview polish — phrasing, structure,
confidence — while native speakers with weaker substance advance. Professional interview
coaching costs $100–200/hour and is effectively unavailable to this group. [Assumption —
directionally well documented, no specific source cited here.]

The agent gives that population a free, private, unlimited mock interviewer that does two
things a generic chatbot does not:

1. **It separates "your answer was weak" from "your English was weak"** — two scores, side
   by side — and explains the difference in the language the user thinks in.
2. **It proves the user got better.** After coaching, the user re-answers *the same
   question*, and the agent scores it again. The before/after is on identical input, so
   the improvement is attributable to the coaching, not to an easier question.

The user may answer in their first language when they cannot express the idea in English.
The agent then shows them the English answer they *could have given*, built from their own
facts. That reframes the gap as language, not ability — which is the actual intervention.

## 2. Goals

1. A user picks a target role and their first language, and runs a 3-question mock
   interview end-to-end in under 10 minutes.
2. Each answer is scored on two separate axes — **content** (structure, specificity,
   ownership) and **English quality** — so the two can move independently.
3. Each answer gets feedback in the user's first language, with an English
   back-translation beside it.
4. Each answer gets a "model answer" in English built strictly from what the user actually
   said, with any missing specifics marked as fill-in prompts rather than invented.
5. After feedback, the user re-answers the same question and sees a before/after score.
6. The session ends with a report: per-question before/after, average lift, and the top 3
   things to work on.
7. The whole thing is built on Strands Agents SDK with a genuine multi-agent structure
   (specialist agents with distinct responsibilities), not one prompt in a loop.

## 3. Non-goals

- Voice input or output. No Transcribe, no Polly — cut entirely, not a stretch goal.
- Web app, hosting, auth, user accounts, or a database.
- Resume parsing, job-board integration, or application tracking.
- Language coverage beyond English and Hindi in the demo. The prompts are
  language-agnostic; only those two are tested and claimed.
- A credential-free replay mode for people cloning the repo.
- Real-time interruption or conversational back-and-forth within a single answer.

## 4. Anti-goals (failure even if it technically works)

- **A chatbot wrapper.** If the architecture is one agent with a long prompt, originality
  and technical execution both collapse. The multi-agent split must be real.
- **A model answer containing facts the user never said.** The target users are exactly
  the people who would memorise an invented detail and repeat it in a real interview. Any
  specific the user did not supply appears as a bracketed prompt — `[how many days late?]`
  — never as a fabricated fact.
- **A fake improvement curve.** The before/after number must come from a real re-scored
  retry, not from the author writing a better answer the second time.
- **Feedback that is generic praise.** The critique must quote the user's own words back.
- **Missing the deadline** because the build grew. Scope is the risk, not skill.

## 5. Constraints

| Constraint | Value | Source |
|---|---|---|
| Total build time | ~5–6 hours, max 1 hr/day | User |
| Team size | Solo | User |
| Deadline | 2026-11-04, 11:59 PM PST | requirements.txt |
| Mandatory qualifier | Complete the Strands SDK workshop on Builder Center | requirements.txt |
| Mandatory deliverables | Agent + Builder Center article + public repo + <3 min public demo video | requirements.txt |
| Prior experience | Has used Strands / Bedrock before | User |
| Demo languages | English primary, Hindi as the second supported language | User |
| Author can verify | English directly; Hindi via the English back-translation | User + Claude's call |
| Target outcome | Credible, complete submission, not an all-out run at top 3 | Claude's call — override if wrong |

## 6. Alternatives considered

The hackathon brief offered three education examples. All three were evaluated.

| Option | Social impact story | Multi-agent fit | Build cost (hrs) | Demo quality | Originality risk |
|---|---|---|---|---|---|
| **A. Mock-interview coach in first language** (chosen) | Strong — direct economic outcome for a sharply defined underserved group | Strong — interviewer / evaluator / coach split is natural | ~4–5 | Strong — real before/after score, emotional story | Low — bilingual bridge + measured retry is a real differentiator |
| B. Textbook chapter → guided practice set | Moderate — crowded space, many existing tools | Weak — mostly one generation step | ~3 | Moderate — hard to show impact in 3 min | High — near-identical to workshop examples |
| C. Leveled reading passages for mixed-level classrooms | Strong — helps under-resourced teachers | Moderate — one agent per reading level is somewhat artificial | ~3 | Weak — output is a wall of text | Moderate |

**Decision:** Option A.
**Rationale:** It is the only one of the three where the multi-agent architecture is
*required* by the problem rather than bolted on, and the only one where improvement is
measurable inside a single 3-minute demo.
**Trade-off accepted:** It is the most build-hours-expensive of the three.
**Reversibility:** Easy through Day 2; hard after.
**Blast radius if wrong:** A weaker submission, not a failed one. No external dependency.

## 7. What it does — user flow

```
$ python -m coach

  Target role?           Customer support representative
  Your first language?   Hindi
  Experience level?      Entry level

  ── Question 1 of 3 ────────────────────────────────────────────
  "Tell me about a time a customer was angry with you.
   What did you do?"

  Your answer (English, Hindi, or a mix — whatever is easier):
  > customer bahut gussa tha about late delivery, I said sorry
  > and gave him refund, he was okay after

  ── Feedback ───────────────────────────────────────────────────
  Content 4/10   Structure 2 · Specificity 3 · Ownership 6
  English 5/10

  आपने जो किया वह सही था, लेकिन आपने यह नहीं बताया कि आपने स्थिति
  को कैसे संभाला। पहले बताइए कि समस्या क्या थी...
  ⤷ (en) What you did was right, but you didn't say how you
         handled the situation. Start by saying what the problem
         was...

  The answer you could have given:
  "A customer called about a delivery that was [how late?].
   I apologised, [what did you check?], and processed a full
   refund. The customer was satisfied."
   ⤷ the bracketed parts are yours to fill in — I won't invent them

  ── Try that question again ────────────────────────────────────
  > A customer called about a delivery that was four days late.
  > I apologised, checked the tracking record to confirm, and
  > processed a full refund the same day. He was satisfied.

  Content 4 → 8   English 5 → 7        ✦ you improved this answer

  ── Question 2 of 3 ────────────────────────────────────────────
  ...

  ── Session report ─────────────────────────────────────────────
  Q1  content 4 → 8    english 5 → 7
  Q2  content 5 → 7    english 5 → 6
  Q3  content 6 → 8    english 6 → 7
  Average lift after coaching:  content +2.7   english +1.3

  Work on:  1. Use the STAR structure — situation first
            2. Give one concrete number in every answer
            3. Say what you learned at the end
```

Interface is a terminal app with `rich` formatting. [Claude's call — fastest path to a
working demo and records cleanly on video. No Streamlit, no web UI.]

## 8. Architecture

Three specialist Strands agents, orchestrated by a deterministic Python session loop.

```
                    session loop (plain Python)
                     per question: ask → score → coach → retry → re-score
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
  InterviewerAgent      EvaluatorAgent          CoachAgent
  role-specific         scores content and      explains the score in the
  questions, one        English quality         user's first language, with
  at a time, held       separately; returns     an English back-translation;
  at a constant         structured output       rewrites the answer in English
  difficulty           with evidence quotes     from the user's own facts only
                              │
                              ▼
                     SessionReport (local JSON)
```

**Decision: deterministic orchestration, not a Strands swarm or orchestrator-agent.**
- *Alternatives:* (a) agents-as-tools with an orchestrator agent, (b) Strands swarm,
  (c) deterministic Python loop calling three agents.
- *Rationale:* A 3-minute demo cannot survive an orchestrator deciding to skip the
  evaluator. The loop is a fixed sequence; the intelligence belongs inside each agent.
- *Trade-off:* Less "look at my swarm" surface for the originality score. The originality
  case rests on the bilingual bridge and the measured retry instead.
- *Risk:* A judge reads "deterministic loop" as "not really multi-agent."
  *Mitigation:* the article states the reliability rationale explicitly — that is an
  engineering judgment worth showing — and the agents are genuinely specialised.
- *Reversibility:* Easy — swapping to agents-as-tools is a small change if time allows.

**Agent responsibilities:**

| Agent | Input | Output | Hard constraints |
|---|---|---|---|
| Interviewer | role, experience level, prior questions | one interview question | No theme repeats; difficulty held flat across the three questions so scores stay comparable |
| Evaluator | question, user answer | Pydantic object: content sub-scores, English-quality score, evidence quotes | Must quote the user's words as evidence; same rubric on first and retry answers |
| Coach | score object, user answer, first language | first-language feedback + English back-translation + English model answer | Model answer may use **only** facts present in the user's answer; gaps become `[bracketed prompts]` |

**Why two score axes:** the product claim is that content and English are separable. One
blended score also breaks comparability when a user answers Q1 in Hindi and Q2 in English.
Two axes make the claim mechanical and visible. [Claude's call.]

**Why the English back-translation:** the author reads English, not Hindi. Printing the
back-translation beside the Hindi lets a wrong or garbled translation be caught on sight,
by the author during the build and by a viewer during the video. [Claude's call.]

**Measurable improvement** (rubric: "measurable improvement for underserved populations"):
per-question before/after on identical input, plus average lift. This is the number the
article and video lead with, and it is causally attributable because the question is
held constant.

## 9. AWS and dependencies

| Thing | Use | Justification |
|---|---|---|
| Strands Agents SDK | All three agents | Mandatory for the hackathon |
| Amazon Bedrock (Claude) | Model provider | Strands default; already familiar |
| `pydantic` | Structured evaluator output | Ships with Strands |
| `rich` | Terminal formatting | Makes the demo video legible — small, justified |

No new infrastructure, no database. Session saved to a local JSON file, **only when the
user confirms at the end** — the pitch says "private," and answers may touch immigration
status or workplace mistreatment, so nothing is persisted by default.

**Build runs in the author's own AWS account**, not the workshop sandbox, which expires
and would take the demo with it. [Claude's call.]

## 10. Plan and time budget

| Day | Date | ~1 hr | Output |
|---|---|---|---|
| 1 | Oct 31 | Complete the Builder Center workshop; confirm Bedrock model access in the author's own account/region | **Qualified to submit** |
| 2 | Nov 1 | **Vertical slice:** one question through all three agents with a stub rubric, printing in the terminal | Something demoable exists |
| 3 | Nov 2 | Real rubric with both score axes, retry round, Hindi feedback + back-translation | Feature complete |
| 4 | Nov 3 | Session report, README, repo public, scripted demo scenario, **article draft** | Shippable |
| 5 | Nov 4 | Record video (~25 min), finish article, submit | **Submitted** |

Day 1 is the hard gate: workshop completion is a qualifying requirement and nothing else
matters without it. Do it first even if the build slips.

**Day 2 is a vertical slice, deliberately.** With a hard 1 hr/day cap, a thin end-to-end
path is always demoable; a half-built layer is not. If a day overruns, the pre-agreed cuts
in order are: (1) the session report collapses to a printed table, (2) Hindi drops to
English-only and the article reframes around the retry loop, (3) question count drops from
three to two. [Claude's call.]

## 11. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Workshop sandbox unavailable or slow | Disqualified | Day 1, first hour, before any code |
| Bedrock model access not enabled in the region | Build blocked | Verify on Day 1 alongside the workshop |
| Scope creep into voice / web UI | Misses deadline | Listed as non-goals; nothing is a stretch goal |
| Retry round doesn't actually raise the score | Headline claim fails | Caught on Day 3, not Day 5; the coach's model answer gives the user something concrete to work from, which is what makes the lift reliable |
| Hindi output wrong in a way the author can't see | Embarrassing error on video | English back-translation printed beside it |
| Devanagari renders badly in the terminal | Bad video | Checked on Day 2 as part of the slice; romanized input accepted so no Indic keyboard is needed |
| Non-deterministic scoring on the day of recording | Lost time re-recording | Recording may be edited or re-taken — the rules require only a public video under three minutes showing the agent working, not one unedited live run |
| Article and video left to the last hour | Rushed, costs 25% of the rubric | Article drafted on Day 4, not Day 5 |

## 12. Open questions

Resolved during brainstorming: the improvement mechanism (retry round), demo languages
(English + Hindi), orchestration pattern (deterministic), interface (CLI).

Still open, none blocking:

1. Project name — "First Language Interview Coach" is a working title.
2. Repo host; must be public by submission.
3. Whether the target really is a complete submission rather than a run at top 3 — if the
   latter, the agents-as-tools swap and a fourth day of polish come back on the table.

## 13. What is left to the builder

- Exact content sub-dimensions and weights within the content score.
- Prompt wording for each agent.
- Question bank strategy: fully generated per role vs. a seeded bank the interviewer
  adapts from.
- Session JSON schema.
- Whether the question count is fixed at three or configurable.
- How the English-quality score is defined operationally (grammar? clarity? both?).

## 14. Calls Claude made — check these

These were settled without asking, because a sensible builder could settle them and the
answer does not change what the project *is*. Override any of them.

1. Model answers never invent facts; gaps are bracketed prompts (§4, §8).
2. Two score axes, content and English, rather than one blended score (§8).
3. English back-translation printed beside first-language feedback (§8).
4. Three questions, not five — each now carries a retry, so that is six scored answers and
   a shorter, tighter video.
5. Build in the author's own AWS account, not the expiring sandbox (§9).
6. No credential-free replay mode; the README states the real prerequisite (Bedrock
   access), rather than claiming anyone can run it in five minutes flat.
7. Polly cut entirely rather than kept as a stretch goal (§3).
8. Session JSON saved only on explicit confirmation (§9).
9. Day 2 is a vertical slice, with pre-agreed cuts if a day overruns (§10).
10. Target outcome assumed to be a complete, credible submission (§5).

---

**Confidence:** Medium-High — the scope fits the time budget with roughly half an hour of
slack, and the author's prior Strands/Bedrock experience removes the largest unknown. The
retry round added about 45 minutes, paid for by dropping from five questions to three. The
main uncertainty is how long the mandatory workshop takes, which is outside our control.

**Change log**

| Date | Change |
|---|---|
| 2026-10-30 | Initial design drafted from brainstorming session |
| 2026-10-30 | Builder check applied: retry round added, two score axes, back-translation, grounding rule for model answers, vertical-slice schedule, question count 5 → 3 |
