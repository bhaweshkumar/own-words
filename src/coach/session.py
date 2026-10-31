from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from coach.models import Coaching, Evaluation, Round, SessionReport

FIRST_ANSWER_PROMPT = "Your answer"
RETRY_PROMPT = (
    "Now try that same question again, in English this time - "
    "the real interview will be in English, so this is the rehearsal"
)

FOCUS_ADVICE = {
    "structure": "Set out the situation, what you did, and how it ended - in that order.",
    "specificity": "Give at least one concrete number or detail in every answer.",
    "ownership": "Say what you did, not what the team did.",
    "english": "Keep sentences short and simple - being clear beats sounding clever.",
}


@dataclass
class CoachAgents:
    next_question: Callable[[list[str]], str]
    evaluate: Callable[[str, str], Evaluation]
    coach: Callable[[str, str, Evaluation], Coaching]


class SessionObserver(Protocol):
    def on_question(self, index: int, total: int, question: str) -> None: ...

    def on_feedback(self, evaluation: Evaluation, coaching: Coaching) -> None: ...

    def on_retry(self, before: Evaluation, after: Evaluation) -> None: ...

    def on_error(self, error: Exception) -> None: ...


def run_session(
    role: str,
    experience: str,
    language: str,
    ask: Callable[[str], str],
    agents: CoachAgents,
    observer: SessionObserver | None = None,
    questions: int = 3,
) -> SessionReport:
    asked: list[str] = []
    rounds: list[Round] = []

    for index in range(1, questions + 1):
        try:
            question = agents.next_question(list(asked))
            asked.append(question)
            _notify(observer, "on_question", index, questions, question)

            first_answer = _ask_until_answered(ask, FIRST_ANSWER_PROMPT)
            first_eval = agents.evaluate(question, first_answer)
            coaching = agents.coach(question, first_answer, first_eval)
            _notify(observer, "on_feedback", first_eval, coaching)

            retry_answer = _ask_until_answered(
                ask, f"{RETRY_PROMPT}\n  {question}\nYour answer"
            )
            retry_eval = agents.evaluate(question, retry_answer)
            _notify(observer, "on_retry", first_eval, retry_eval)

            rounds.append(
                Round(
                    question=question,
                    first_answer=first_answer,
                    first_eval=first_eval,
                    coaching=coaching,
                    retry_answer=retry_answer,
                    retry_eval=retry_eval,
                )
            )
        except Exception as error:
            _notify(observer, "on_error", error)
            break

    return SessionReport(
        role=role,
        language=language,
        rounds=rounds,
        focus_areas=focus_areas(rounds),
    )


def focus_areas(rounds: list[Round]) -> list[str]:
    """The weakest dimensions of the first attempts - the habits to work on."""
    if not rounds:
        return []
    firsts = [r.first_eval for r in rounds]
    means = {
        "structure": _mean(e.content.structure for e in firsts),
        "specificity": _mean(e.content.specificity for e in firsts),
        "ownership": _mean(e.content.ownership for e in firsts),
    }
    # English only earns a place if there was English to score. Advice drawn
    # from a score the evaluator declined to give is advice about nothing.
    in_english = [e.english for e in firsts if e.answered_in_english]
    if in_english:
        means["english"] = _mean(in_english)
    weakest = sorted(means, key=lambda name: means[name])[:3]
    return [FOCUS_ADVICE[name] for name in weakest]


def unique_path(path: Path) -> Path:
    """Never silently overwrite an earlier session - those are the user's own
    answers, and they only get saved because they asked."""
    path = Path(path)
    if not path.exists():
        return path
    for n in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{n}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"too many saved sessions beside {path}")


def maybe_save(report: SessionReport, answer: str, path: Path) -> bool:
    if answer.strip().lower() not in {"y", "yes"}:
        return False
    Path(path).write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return True


def _ask_until_answered(ask: Callable[[str], str], prompt: str) -> str:
    while True:
        answer = ask(prompt)
        if answer.strip():
            return answer


def _notify(observer, method: str, *args) -> None:
    handler = getattr(observer, method, None)
    if handler is not None:
        handler(*args)


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values)
