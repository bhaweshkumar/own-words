import sys
from pathlib import Path

from rich.console import Console

from coach.agents import DISCOVERY_HINT, live_agents
from coach.display import ConsoleObserver, render_report
from coach.session import maybe_save, run_session, unique_path

DEFAULT_ROLE = "Customer support representative"
DEFAULT_EXPERIENCE = "Entry level"
DEFAULT_LANGUAGE = "English"
SESSION_PATH = Path("session.json")


def ask(prompt: str) -> str:
    try:
        return input(f"{prompt}: ")
    except EOFError:
        # Ctrl-D, or a piped demo script running out of lines. An empty
        # string is already handled everywhere it can land.
        return ""


def collect_setup(ask):
    role = ask("Target role") or DEFAULT_ROLE
    experience = ask("Your experience level") or DEFAULT_EXPERIENCE
    language = ask("Your first language") or DEFAULT_LANGUAGE
    return role.strip(), experience.strip(), language.strip()


def main(argv: list[str] | None = None) -> int:
    console = Console()

    console.rule("Own Words · interview coach")
    console.print(
        "Answer in English, in your own language, or a mix — whatever is easier.\n",
        style="dim",
    )

    role, experience, language = collect_setup(ask)

    try:
        agents = live_agents(role, experience, language)
    except Exception as error:
        # A stale AWS profile, a region without Bedrock access or an unset
        # model id all land here. None of them deserve a traceback.
        message = str(error)
        if DISCOVERY_HINT not in message:
            message = f"Could not reach Bedrock: {message}\n\n{DISCOVERY_HINT}"
        print(message, file=sys.stderr)
        return 1

    try:
        report = run_session(
            role=role,
            experience=experience,
            language=language,
            ask=ask,
            agents=agents,
            observer=ConsoleObserver(console),
        )
    except KeyboardInterrupt:
        console.print("\nStopped.", style="dim")
        return 130

    render_report(console, report)

    if report.rounds:
        path = unique_path(SESSION_PATH)
        if maybe_save(report, ask("\nSave this session to a file? (y/n)"), path):
            console.print(f"Saved to {path}", style="dim")
    return 0
