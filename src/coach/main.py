import sys
from pathlib import Path

from rich.console import Console

from coach.agents import live_agents
from coach.display import ConsoleObserver, render_report
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


def main(argv: list[str] | None = None) -> int:
    console = Console()

    def ask(prompt: str) -> str:
        return input(f"{prompt}: ")

    console.rule("First Language Interview Coach")
    console.print(
        "Answer in English, in your own language, or a mix — whatever is easier.\n",
        style="dim",
    )

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
        observer=ConsoleObserver(console),
    )
    render_report(console, report)

    if report.rounds:
        saved = maybe_save(
            report, ask("\nSave this session to a file? (y/n)"), SESSION_PATH
        )
        if saved:
            console.print(f"Saved to {SESSION_PATH}", style="dim")
    return 0
