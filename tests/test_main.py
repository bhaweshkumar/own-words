from coach.main import collect_setup, main
from coach.models import SessionReport


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
