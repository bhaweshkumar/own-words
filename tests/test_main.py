from coach.main import ask, collect_setup, main
from coach.models import SessionReport


def test_ask_returns_empty_on_end_of_input_instead_of_raising(monkeypatch):
    """Ctrl-D, or a piped demo script running out of lines, must not end the
    run with an EOFError traceback."""

    def raise_eof(*_args):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    assert ask("Your answer") == ""


def test_main_reports_a_broken_aws_profile_without_a_traceback(monkeypatch, capsys):
    """bedrock_model() raises botocore errors, not just RuntimeError."""
    import coach.main as main_module

    class ProfileNotFound(Exception):
        pass

    def explode(*_args, **_kwargs):
        raise ProfileNotFound("The config profile (stale-sso) could not be found")

    monkeypatch.setattr(main_module, "live_agents", explode)
    monkeypatch.setattr("builtins.input", lambda *_: "Nurse")

    assert main([]) == 1
    captured = capsys.readouterr()
    assert "stale-sso" in captured.err
    assert "Traceback" not in captured.err


def test_main_does_not_print_the_model_id_hint_twice(monkeypatch, capsys):
    import coach.main as main_module

    monkeypatch.delenv("COACH_MODEL_ID", raising=False)
    monkeypatch.setattr("builtins.input", lambda *_: "Nurse")

    main([])
    assert capsys.readouterr().err.count("list-inference-profiles") == 1


def test_main_exits_cleanly_when_the_user_presses_ctrl_c(monkeypatch):
    import coach.main as main_module

    def interrupt(**_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(main_module, "live_agents", lambda *a, **k: object())
    monkeypatch.setattr(main_module, "run_session", interrupt)
    monkeypatch.setattr("builtins.input", lambda *_: "Nurse")

    assert main([]) == 130


def scripted(answers):
    remaining = list(answers)

    def ask(_prompt):
        return remaining.pop(0)

    return ask


def test_setup_collects_role_experience_and_language():
    assert collect_setup(
        scripted(["Customer support representative", "Entry level", "Hindi"])
    ) == ("Customer support representative", "Entry level", "Hindi")


def test_setup_defaults_the_language_to_english_when_left_blank():
    assert collect_setup(scripted(["Nurse", "Entry level", ""]))[2] == "English"


def test_setup_defaults_blank_role_and_experience_rather_than_sending_empty_strings():
    role, experience, _language = collect_setup(scripted(["", "", "Hindi"]))
    assert role.strip()
    assert experience.strip()


def test_main_reports_a_clear_error_when_the_model_id_is_unset(monkeypatch, capsys):
    monkeypatch.delenv("COACH_MODEL_ID", raising=False)
    monkeypatch.setattr("builtins.input", lambda *_: "Nurse")
    assert main([]) == 1
    captured = capsys.readouterr()
    assert "COACH_MODEL_ID" in captured.err
    assert "Traceback" not in captured.err


def test_main_does_not_write_a_session_file_when_the_session_produced_nothing(
    monkeypatch, tmp_path
):
    """A session that failed on its first Bedrock call must not leave an
    empty session.json behind, nor ask whether to save one."""
    import coach.main as main_module

    empty = SessionReport(role="Nurse", language="Hindi", rounds=[], focus_areas=[])
    monkeypatch.setattr(main_module, "SESSION_PATH", tmp_path / "session.json")
    monkeypatch.setattr(main_module, "live_agents", lambda *a, **k: object())
    monkeypatch.setattr(main_module, "run_session", lambda **kwargs: empty)
    monkeypatch.setattr("builtins.input", lambda *_: "Nurse")

    assert main([]) == 0
    assert not (tmp_path / "session.json").exists()
