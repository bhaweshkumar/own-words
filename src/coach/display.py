from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from coach.models import Coaching, Evaluation, SessionReport


def render_question(console: Console, index: int, total: int, question: str) -> None:
    console.print()
    console.print(
        Panel(
            Text(question, style="bold"),
            title=f"Question {index} of {total}",
            title_align="left",
            border_style="cyan",
        )
    )


def render_feedback(
    console: Console, evaluation: Evaluation, coaching: Coaching
) -> None:
    content = evaluation.content
    scores = Text()
    scores.append(f"Content {evaluation.content_total}/10", style="bold")
    scores.append(
        f"   structure {content.structure} · specificity {content.specificity}"
        f" · ownership {content.ownership}\n",
        style="dim",
    )
    if evaluation.answered_in_english:
        scores.append(f"English {evaluation.english}/10", style="bold")
    else:
        # The candidate was invited to answer in their own language; a number
        # here would read as failed English rather than as that choice.
        scores.append("English —", style="bold")
        scores.append("   not in English, so not scored", style="dim")

    for quote in evaluation.evidence:
        scores.append(f"\n  “{quote}”", style="italic dim")

    body = Text()
    body.append(coaching.feedback_native + "\n")
    body.append(f"⤷ (en) {coaching.feedback_english}", style="dim italic")

    answer = Text()
    answer.append(coaching.model_answer + "\n")
    answer.append(
        "⤷ anything in [brackets] is yours to fill in — it was not invented for you",
        style="dim italic",
    )

    console.print()
    console.print(Panel(scores, title="Feedback", title_align="left", border_style="yellow"))
    console.print(body)
    console.print()
    console.print(
        Panel(
            answer,
            title="The answer you could have given",
            title_align="left",
            border_style="green",
        )
    )


def render_retry(console: Console, before: Evaluation, after: Evaluation) -> None:
    lift = after.content_total - before.content_total
    english_lift = _english_lift(before, after)

    line = Text()
    line.append("Content ", style="bold")
    line.append(f"{before.content_total} → {after.content_total}", style=_delta_style(lift))
    line.append("   English ", style="bold")
    if english_lift is None:
        line.append("not scored", style="dim")
    else:
        line.append(f"{before.english} → {after.english}", style=_delta_style(english_lift))

    if lift > 0 and (english_lift is None or english_lift >= 0):
        line.append("        ✦ you improved this answer", style="green")

    console.print()
    console.print(line)
    if english_lift is None:
        console.print(
            "  one of these answers was not in English, so there was no English "
            "to compare",
            style="dim italic",
        )


def render_report(console: Console, report: SessionReport) -> None:
    table = Table(title="Session report", title_justify="left", border_style="cyan")
    table.add_column("")
    table.add_column("Content", justify="center")
    table.add_column("English", justify="center")
    for index, round_ in enumerate(report.rounds, start=1):
        english = (
            f"{round_.first_eval.english} → {round_.retry_eval.english}"
            if round_.english_lift is not None
            else "—"
        )
        table.add_row(
            f"Q{index}",
            f"{round_.first_eval.content_total} → {round_.retry_eval.content_total}",
            english,
        )

    console.print()
    console.print(table)
    if report.rounds:
        summary = (
            f"Average lift after coaching:  "
            f"content {report.average_content_lift:+.1f}"
        )
        if report.average_english_lift is not None:
            summary += f"   english {report.average_english_lift:+.1f}"
        console.print(summary)
    console.print()
    console.print(Text("Work on:", style="bold"))
    for area in report.focus_areas:
        console.print(f"  • {area}")


class ConsoleObserver:
    def __init__(self, console: Console):
        self.console = console

    def on_question(self, index: int, total: int, question: str) -> None:
        render_question(self.console, index, total, question)

    def on_feedback(self, evaluation: Evaluation, coaching: Coaching) -> None:
        render_feedback(self.console, evaluation, coaching)

    def on_retry(self, before: Evaluation, after: Evaluation) -> None:
        render_retry(self.console, before, after)

    def on_error(self, error: Exception) -> None:
        self.console.print()
        self.console.print(
            Text(f"The session stopped early: {error}", style="red")
        )


def _english_lift(before: Evaluation, after: Evaluation) -> int | None:
    if not (before.answered_in_english and after.answered_in_english):
        return None
    return after.english - before.english


def _delta_style(lift: int) -> str:
    if lift > 0:
        return "bold green"
    if lift < 0:
        return "bold red"
    return "bold"
