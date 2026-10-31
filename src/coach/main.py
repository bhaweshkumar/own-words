import sys
from pathlib import Path

from coach.agents import live_agents
from coach.models import Coaching, Evaluation, SessionReport
from coach.session import maybe_save, run_session

DEFAULT_ROLE = "Customer support representative"
DEFAULT_EXPERIENCE = "Entry level"
DEFAULT_LANGUAGE = "English"
SESSION_PATH = Path("session.json")


def collect_setup(ask):
    role = ask("Target role") or DEFAULT_ROLE
    experience = ask("Your experience level") or DEFAULT_EXPERIENCE
    language = ask("Your first language") or DEFAULT_LANGUAGE
    return role.strip(), experience.strip(), language.strip()


class PlainObserver:
    """Prints with bare print(). Task 5 replaces this with the rich renderer."""

    def on_question(self, index, total, question):
        print(f"\n--- Question {index} of {total} ---\n{question}\n")

    def on_feedback(self, evaluation: Evaluation, coaching: Coaching):
        print(
            f"\nContent {evaluation.content_total}/10   "
            f"English {evaluation.english}/10"
        )
        print(f"\n{coaching.feedback_native}")
        print(f"(en) {coaching.feedback_english}")
        print(f"\nThe answer you could have given:\n{coaching.model_answer}\n")

    def on_retry(self, before: Evaluation, after: Evaluation):
        print(
            f"\nContent {before.content_total} -> {after.content_total}   "
            f"English {before.english} -> {after.english}\n"
        )

    def on_error(self, error: Exception):
        print(f"\nThe session stopped early: {error}\n", file=sys.stderr)


def print_report(report: SessionReport) -> None:
    print("\n=== Session report ===")
    for index, round_ in enumerate(report.rounds, start=1):
        print(
            f"Q{index}  content {round_.first_eval.content_total} -> "
            f"{round_.retry_eval.content_total}   "
            f"english {round_.first_eval.english} -> {round_.retry_eval.english}"
        )
    if report.rounds:
        print(
            f"\nAverage lift after coaching:  "
            f"content {report.average_content_lift:+.1f}   "
            f"english {report.average_english_lift:+.1f}"
        )
    print("\nWork on:")
    for area in report.focus_areas:
        print(f"  - {area}")


def main(argv: list[str] | None = None) -> int:
    def ask(prompt: str) -> str:
        return input(f"{prompt}: ")

    role, experience, language = collect_setup(ask)

    try:
        agents = live_agents(role, experience, language)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    report = run_session(
        role=role,
        experience=experience,
        language=language,
        ask=ask,
        agents=agents,
        observer=PlainObserver(),
    )
    print_report(report)

    if report.rounds:
        saved = maybe_save(report, ask("\nSave this session to a file? (y/n)"), SESSION_PATH)
        if saved:
            print(f"Saved to {SESSION_PATH}")
    return 0
