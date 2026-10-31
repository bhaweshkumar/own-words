# First Language Interview Coach — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A terminal mock-interview agent that scores an answer on content and English separately, explains the critique in the user's first language, and proves improvement by re-scoring a coached retry of the same question.

**Architecture:** Three specialist Strands agents (interviewer, evaluator, coach) behind plain-function adapters, driven by a deterministic Python session loop. The loop takes its agents as injected callables, so every test runs without AWS. Rendering is a separate module so the loop stays pure.

**Tech Stack:** Python 3.11+, Strands Agents SDK, Amazon Bedrock, Pydantic, `rich`, pytest

**Spec:** [20261030-interview-coach-design.md](20261030-interview-coach-design.md)

## Global Constraints

- Python 3.11 or newer.
- Dependencies limited to: `strands-agents`, `pydantic`, `rich`, `pytest`. No others without justification.
- **No test may make a network call.** The session loop receives agents as injected callables; tests pass fakes.
- Bedrock model ID is **never hardcoded**. It is read from the `COACH_MODEL_ID` environment variable, with region from `AWS_REGION`. Model availability varies per account and region, so the exact ID is discovered on Day 1 with `aws bedrock list-inference-profiles --region <region>` and recorded in the README.
- Scores are integers 0–10 on every axis.
- Content and English are **separate** scores and are never blended into one number.
- The coach's model answer may contain only facts present in the user's answer. Missing specifics appear as `[bracketed prompts]`.
- Default session length is 3 questions, each with exactly one retry round.
- Session JSON is written only after explicit user confirmation.
- Commit after every task.

## Review Focus

Input classes the spec implies but no feature task naturally exercises. Each line's test is added to the task that owns the code.

1. **Empty or whitespace-only answer** — the user presses enter without typing. Must not be sent to the evaluator or scored; the loop re-prompts. (Task 3)
2. **Answer written in Devanagari or romanized Hindi** — non-ASCII and code-mixed text must pass through the loop and render without a `UnicodeEncodeError`. (Task 5)
3. **Retry scores lower than the first attempt** — the lift is negative and must be reported as negative, never clamped to zero. A coach that makes things worse must be visible. (Task 1)
4. **Bedrock throttles or errors mid-session** — rounds already completed must survive; the session ends early with a partial report rather than losing everything. (Task 3)
5. **An answer containing no usable facts** ("I don't know") — the coach's model answer is then almost entirely brackets, which is correct behavior, not a bug; nothing downstream may assume the model answer has content. (Task 4)

---

### Task 1: Project skeleton and data models

**Files:**
- Create: `pyproject.toml`, `src/coach/__init__.py`, `src/coach/models.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Consumes: nothing
- Produces: `ContentScore`, `Evaluation`, `Coaching`, `Round`, `SessionReport` — all Pydantic `BaseModel`s, imported by every later task.

- [ ] **Step 1: Write the failing tests**

```python
from coach.models import ContentScore, Evaluation, Coaching, Round, SessionReport

def _evaluation(structure, specificity, ownership, english):
    return Evaluation(
        content=ContentScore(structure=structure, specificity=specificity, ownership=ownership),
        english=english,
        evidence=["I said sorry"],
    )

def test_content_total_is_the_rounded_mean_of_the_three_subscores():
    assert _evaluation(2, 3, 6, 5).content_total == 4

def test_round_reports_lift_on_both_axes():
    r = Round(
        question="Tell me about a time a customer was angry.",
        first_answer="I said sorry and gave refund",
        first_eval=_evaluation(2, 3, 6, 5),
        coaching=Coaching(feedback_native="...", feedback_english="...", model_answer="..."),
        retry_answer="A customer called about a delivery four days late...",
        retry_eval=_evaluation(8, 8, 8, 7),
    )
    assert r.content_lift == 4
    assert r.english_lift == 2

def test_negative_lift_is_reported_as_negative():
    r = Round(
        question="q", first_answer="a", first_eval=_evaluation(8, 8, 8, 8),
        coaching=Coaching(feedback_native="...", feedback_english="...", model_answer="..."),
        retry_answer="b", retry_eval=_evaluation(4, 4, 4, 5),
    )
    assert r.content_lift == -4
    assert r.english_lift == -3

def test_average_lifts_over_a_session():
    def rnd(before, after):
        return Round(
            question="q", first_answer="a", first_eval=_evaluation(before, before, before, before),
            coaching=Coaching(feedback_native="x", feedback_english="x", model_answer="x"),
            retry_answer="b", retry_eval=_evaluation(after, after, after, after),
        )
    report = SessionReport(
        role="Customer support representative", language="Hindi",
        rounds=[rnd(4, 8), rnd(5, 7), rnd(6, 8)],
        focus_areas=["Use the STAR structure", "Give one concrete number", "Say what you learned"],
    )
    assert report.average_content_lift == 2.0
    assert report.average_english_lift == 2.0

def test_scores_outside_zero_to_ten_are_rejected():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ContentScore(structure=11, specificity=5, ownership=5)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'coach'`

- [ ] **Step 3: Create `pyproject.toml`**

Package name `coach`, `src/` layout, `requires-python = ">=3.11"`, dependencies `strands-agents`, `pydantic`, `rich`; `pytest` as a dev dependency.

- [ ] **Step 4: Implement the models in `src/coach/models.py`**

Sub-scores are `int` fields constrained to 0–10 (`Field(ge=0, le=10)`). `Evaluation.content_total`, `Round.content_lift`, `Round.english_lift`, `SessionReport.average_content_lift` and `SessionReport.average_english_lift` are `@property`, not stored fields. `Coaching` holds three strings: `feedback_native`, `feedback_english`, `model_answer`. `Evaluation.evidence` is `list[str]`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: PASS (5 tests)

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/coach tests/test_models.py
git commit -m "feat: add session data models with separate content and English scores"
```

---

### Task 2: Strands agent factories

**Files:**
- Create: `src/coach/agents.py`
- Create: `tests/test_agents.py`

**Interfaces:**
- Consumes: `Evaluation`, `Coaching` from `coach.models`
- Produces:
  - `bedrock_model() -> BedrockModel`
  - `build_interviewer(role: str, experience: str) -> Agent`
  - `build_evaluator() -> Agent`
  - `build_coach(language: str) -> Agent`

`live_agents` also lives in this module but is written in Task 3, because it returns the `CoachAgents` dataclass that Task 3 defines.

- [ ] **Step 1: Write the failing tests**

These assert on prompt content, not on model output — no network call.

```python
import pytest
from coach.agents import build_interviewer, build_evaluator, build_coach, bedrock_model

def test_bedrock_model_requires_an_explicit_model_id(monkeypatch):
    monkeypatch.delenv("COACH_MODEL_ID", raising=False)
    with pytest.raises(RuntimeError) as exc:
        bedrock_model()
    assert "COACH_MODEL_ID" in str(exc.value)

def test_coach_prompt_names_the_users_language():
    prompt = build_coach("Hindi").system_prompt
    assert "Hindi" in prompt

def test_coach_prompt_forbids_inventing_facts_and_requires_brackets():
    prompt = build_coach("Hindi").system_prompt.lower()
    assert "only facts" in prompt or "never invent" in prompt
    assert "[" in prompt

def test_coach_prompt_requires_an_english_back_translation():
    assert "back-translation" in build_coach("Hindi").system_prompt.lower()

def test_evaluator_prompt_requires_quoting_the_answer_as_evidence():
    assert "quote" in build_evaluator().system_prompt.lower()

def test_interviewer_prompt_holds_difficulty_flat_and_names_the_role():
    prompt = build_interviewer("Customer support representative", "Entry level").system_prompt
    assert "Customer support representative" in prompt
    assert "difficulty" in prompt.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_agents.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'coach.agents'`

- [ ] **Step 3: Implement `bedrock_model()` in `src/coach/agents.py`**

Reads `COACH_MODEL_ID` from the environment and raises `RuntimeError` naming the variable and the discovery command if it is unset. Reads `AWS_REGION`, defaulting to `us-east-1`. Returns `strands.models.BedrockModel(model_id=..., region_name=...)`.

- [ ] **Step 4: Implement the three builders in `src/coach/agents.py`**

Each returns `strands.Agent(model=bedrock_model(), system_prompt=...)`. The system prompts carry the hard constraints from the spec's §8 table:

- Interviewer: asks one question at a time for the given role and experience level, never repeats a theme, and **holds difficulty flat across the session so scores stay comparable**.
- Evaluator: scores `structure`, `specificity`, `ownership` and `english` 0–10 and must quote the user's own words in `evidence`. Same rubric applies to first and retry answers.
- Coach: writes feedback in the named language, then an English back-translation of that same feedback, then a model answer in English that uses **only facts present in the user's answer**, with every missing specific written as a `[bracketed prompt]`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_agents.py -v`
Expected: PASS (6 tests)

- [ ] **Step 6: Commit**

```bash
git add src/coach/agents.py tests/test_agents.py
git commit -m "feat: add interviewer, evaluator and coach agent factories"
```

---

### Task 3: Session loop

**Files:**
- Create: `src/coach/session.py`
- Create: `tests/test_session.py`
- Modify: `src/coach/agents.py` (add `live_agents`)

**Interfaces:**
- Consumes: all models from `coach.models`; the builders from `coach.agents`
- Produces:
  - `CoachAgents` — a dataclass of three callables:
    - `next_question: Callable[[list[str]], str]` — takes questions already asked, returns the next one
    - `evaluate: Callable[[str, str], Evaluation]` — `(question, answer)`
    - `coach: Callable[[str, str, Evaluation], Coaching]` — `(question, answer, evaluation)`
  - `run_session(role: str, experience: str, language: str, ask: Callable[[str], str], agents: CoachAgents, observer: SessionObserver | None = None, questions: int = 3) -> SessionReport`
  - `SessionObserver` — a Protocol with `on_question(index, total, question)`, `on_feedback(evaluation, coaching)`, `on_retry(before, after)`. Task 5 implements it.
  - `maybe_save(report: SessionReport, answer: str, path: Path) -> bool` — writes the JSON only when `answer` is an affirmative; returns whether it wrote.
  - `live_agents(role: str, experience: str, language: str) -> CoachAgents` — added to `coach/agents.py` in step 4 of this task.
- `ask` receives a prompt string and returns the user's typed line. `live_agents` wires the Task 2 builders: interviewer via `str(agent(...))`, evaluator and coach via `agent.structured_output(Evaluation, ...)` / `agent.structured_output(Coaching, ...)`.

- [ ] **Step 1: Write the failing tests**

A fake `CoachAgents` whose `evaluate` returns a scripted sequence of evaluations, and an `ask` that pops from a scripted list of answers.

```python
def test_each_question_runs_ask_score_coach_retry_rescore_in_order():
    # three questions, so six answers and six evaluations
    report = run_session(..., ask=scripted(["a1","r1","a2","r2","a3","r3"]), agents=fake)
    assert len(report.rounds) == 3
    assert [r.first_answer for r in report.rounds] == ["a1", "a2", "a3"]
    assert [r.retry_answer for r in report.rounds] == ["r1", "r2", "r3"]

def test_retry_is_scored_on_the_same_question_as_the_first_attempt():
    report = run_session(...)
    assert fake.evaluate_calls[0][0] == fake.evaluate_calls[1][0]

def test_the_interviewer_is_told_which_questions_were_already_asked():
    run_session(...)
    assert fake.next_question_calls[-1] == ["q1", "q2"]

def test_an_empty_answer_reprompts_and_is_never_evaluated():   # Review Focus 1
    ask = scripted(["", "   ", "a real answer", "a retry", ...])
    run_session(..., ask=ask)
    assert "" not in [call[1] for call in fake.evaluate_calls]

def test_an_error_mid_session_returns_the_rounds_already_completed():   # Review Focus 4
    fake.evaluate_raises_on_call(3)   # partway through question 2
    report = run_session(..., questions=3)
    assert len(report.rounds) == 1

def test_the_observer_is_notified_for_each_question_feedback_and_retry():
    run_session(..., observer=recording_observer)
    assert recording_observer.questions == 3
    assert recording_observer.feedbacks == 3
    assert recording_observer.retries == 3

def test_maybe_save_writes_only_on_an_affirmative_answer(tmp_path):
    path = tmp_path / "session.json"
    assert maybe_save(report, "n", path) is False
    assert not path.exists()
    assert maybe_save(report, "y", path) is True
    assert path.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_session.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'coach.session'`

- [ ] **Step 3: Implement `CoachAgents`, `SessionObserver` and `run_session` in `src/coach/session.py`**

The loop per question: get the question, `ask` until a non-blank answer, evaluate, coach, `ask` for the retry (also non-blank), evaluate again, append the `Round`. Wrap each question's work so any exception ends the session and returns a `SessionReport` with the rounds completed so far. `focus_areas` for the report is the three most common weaknesses — derive from the lowest-scoring sub-dimensions across rounds; the builder picks the exact derivation.

- [ ] **Step 4: Implement `live_agents` in `src/coach/agents.py`**

Wires the three builders into a `CoachAgents`. The interviewer call passes the already-asked questions in the prompt; evaluator and coach use `structured_output`.

- [ ] **Step 5: Implement `maybe_save` in `src/coach/session.py`**

Affirmative means `answer.strip().lower()` in `{"y", "yes"}`. Writes `report.model_dump_json(indent=2)`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_session.py -v`
Expected: PASS (7 tests)

- [ ] **Step 7: Commit**

```bash
git add src/coach/session.py src/coach/agents.py tests/test_session.py
git commit -m "feat: add deterministic session loop with coached retry round"
```

---

### Task 4: CLI entry point — the vertical slice

**Files:**
- Create: `src/coach/__main__.py`
- Create: `tests/test_main.py`

**Interfaces:**
- Consumes: `run_session`, `maybe_save`, `live_agents`
- Produces: `main(argv: list[str] | None = None) -> int` and `collect_setup(ask: Callable[[str], str]) -> tuple[str, str, str]` returning `(role, experience, language)`

- [ ] **Step 1: Write the failing tests**

```python
def test_setup_collects_role_experience_and_language():
    assert collect_setup(scripted(["Customer support representative", "Entry level", "Hindi"])) == (
        "Customer support representative", "Entry level", "Hindi")

def test_setup_defaults_the_language_to_english_when_left_blank():
    assert collect_setup(scripted(["Nurse", "Entry level", ""]))[2] == "English"

def test_main_reports_a_clear_error_when_the_model_id_is_unset(monkeypatch, capsys):
    monkeypatch.delenv("COACH_MODEL_ID", raising=False)
    assert main([]) == 1
    assert "COACH_MODEL_ID" in capsys.readouterr().err

def test_a_model_answer_that_is_entirely_brackets_is_still_printed(capsys):   # Review Focus 5
    # coaching.model_answer == "[what was the situation?] [what did you do?]"
    ...
    assert "[what was the situation?]" in capsys.readouterr().out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'coach.__main__'`

- [ ] **Step 3: Implement `collect_setup` and `main` in `src/coach/__main__.py`**

`main` collects setup, builds `live_agents`, runs the session with plain `print` output for now (Task 5 replaces it), prints the report, then asks whether to save and calls `maybe_save`. A `RuntimeError` from `bedrock_model()` is caught and printed to stderr with exit code 1 — never a traceback.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -v`
Expected: PASS (all tasks' tests)

- [ ] **Step 5: Verify the slice end to end against Bedrock**

Run: `COACH_MODEL_ID=<id from Day 1> python -m coach`
Expected: a real question appears, an answer is scored, feedback prints, the retry is scored, a report prints. This is the first real spend — one session only.

- [ ] **Step 6: Commit**

```bash
git add src/coach/__main__.py tests/test_main.py
git commit -m "feat: add CLI entry point running a full coached session"
```

---

### Task 5: Rich rendering

**Files:**
- Create: `src/coach/display.py`
- Create: `tests/test_display.py`
- Modify: `src/coach/__main__.py` (swap `print` for the observer)

**Interfaces:**
- Consumes: `Evaluation`, `Coaching`, `SessionReport`, `SessionObserver`
- Produces, all in `coach.display`:
  - `render_question(console: Console, index: int, total: int, question: str) -> None`
  - `render_feedback(console: Console, evaluation: Evaluation, coaching: Coaching) -> None`
  - `render_retry(console: Console, before: Evaluation, after: Evaluation) -> None`
  - `render_report(console: Console, report: SessionReport) -> None`
  - `ConsoleObserver(console: Console)` — implements `SessionObserver` by delegating to the first three

- [ ] **Step 1: Write the failing tests**

Each test builds a `rich.console.Console(record=True, width=80)`, calls the render function, and asserts on `console.export_text()`. The `*_text` helpers below are local test fixtures that do that wrapping.

```python
def test_feedback_shows_content_and_english_as_separate_scores():
    text = render_feedback_text(evaluation=_evaluation(2, 3, 6, 5), coaching=...)
    assert "Content 4/10" in text
    assert "English 5/10" in text

def test_feedback_shows_the_native_text_and_its_english_back_translation():
    text = render_feedback_text(coaching=Coaching(
        feedback_native="आपने जो किया वह सही था",
        feedback_english="What you did was right",
        model_answer="..."))
    assert "आपने जो किया वह सही था" in text      # Review Focus 2
    assert "What you did was right" in text

def test_retry_result_shows_the_before_and_after_on_both_axes():
    text = render_retry_text(before=_evaluation(2,3,6,5), after=_evaluation(8,8,8,7))
    assert "4 → 8" in text
    assert "5 → 7" in text

def test_report_shows_per_question_rows_and_average_lift():
    text = render_report_text(report)
    assert "Average lift" in text

def test_devanagari_renders_without_a_unicode_error():   # Review Focus 2
    render_report_text(report_with_devanagari_focus_areas())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_display.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'coach.display'`

- [ ] **Step 3: Implement `src/coach/display.py`**

`rich` panels for the question and the feedback, a table for the report. Score lines read `Content {content_total}/10` and `English {english}/10`; the retry line reads `{before} → {after}` per axis. Native feedback prints above its back-translation, which is visually marked as a translation.

- [ ] **Step 4: Swap `__main__` over to `ConsoleObserver` and `render_report`**

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest -v`
Expected: PASS

- [ ] **Step 6: Check Devanagari in the real terminal at video resolution**

Run: `COACH_MODEL_ID=<id> python -m coach` with language `Hindi`, and confirm the Devanagari is legible at the font size you will record at. If it is not, the fix is a font change, not a code change — find out now, not on recording day.

- [ ] **Step 7: Commit**

```bash
git add src/coach/display.py tests/test_display.py src/coach/__main__.py
git commit -m "feat: render feedback, retry deltas and session report with rich"
```

---

### Task 6: README and repo readiness

**Files:**
- Create: `README.md`, `.gitignore`
- Modify: none

**Interfaces:**
- Consumes: everything
- Produces: nothing code depends on

- [ ] **Step 1: Write `README.md`**

Covers: what the agent does and who it is for (two paragraphs from the spec's §1); the real prerequisites (an AWS account with Bedrock model access granted, credentials configured, Python 3.11+); the Day 1 discovery command for `COACH_MODEL_ID`; install and run; the three-agent architecture with the reason the orchestration is deterministic; and an explicit statement that it is demonstrated in English and Hindi and that the prompts are language-agnostic but untested elsewhere. Do not claim anyone can run it in five minutes.

- [ ] **Step 2: Write `.gitignore`**

`__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.venv/`, `session*.json` — saved sessions contain the user's own answers and must never be committed.

- [ ] **Step 3: Verify the full suite and a clean run**

Run: `pytest -v`
Expected: PASS, no network calls.

- [ ] **Step 4: Commit and make the repo public**

```bash
git add README.md .gitignore
git commit -m "docs: add README with real prerequisites and architecture rationale"
```

---

## Task-to-day mapping

| Day | Date | Tasks |
|---|---|---|
| 1 | Oct 31 | Builder Center workshop; discover `COACH_MODEL_ID`; confirm Bedrock access. No code. |
| 2 | Nov 1 | Tasks 1–3 |
| 3 | Nov 2 | Tasks 4–5 — the slice runs end to end against Bedrock |
| 4 | Nov 3 | Task 6; draft the Builder Center article |
| 5 | Nov 4 | Record the demo video; finish the article; submit |

If a day overruns, the spec's pre-agreed cuts apply in order: the report collapses to a plain table, Hindi drops to English-only, question count drops from three to two.
