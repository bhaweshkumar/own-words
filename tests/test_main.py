from coach.main import PlainObserver, collect_setup, main
from coach.models import Coaching, ContentScore, Evaluation


def scripted(answers):
    remaining = list(answers)

    def ask(_prompt):
        return remaining.pop(0)

    return ask


def _evaluation(score):
    return Evaluation(
        content=ContentScore(structure=score, specificity=score, ownership=score),
        english=score,
        evidence=["quoted"],
    )


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


def test_a_model_answer_that_is_entirely_brackets_is_still_printed(capsys):
    coaching = Coaching(
        feedback_native="native",
        feedback_english="english",
        model_answer="[what was the situation?] [what did you do?]",
    )
    PlainObserver().on_feedback(_evaluation(3), coaching)
    assert "[what was the situation?]" in capsys.readouterr().out


def test_the_plain_observer_shows_content_and_english_as_separate_scores(capsys):
    PlainObserver().on_feedback(
        _evaluation(4),
        Coaching(feedback_native="n", feedback_english="e", model_answer="m"),
    )
    out = capsys.readouterr().out
    assert "Content 4/10" in out
    assert "English 4/10" in out


def test_the_plain_observer_shows_the_retry_delta_on_both_axes(capsys):
    PlainObserver().on_retry(_evaluation(4), _evaluation(8))
    out = capsys.readouterr().out
    assert "4 -> 8" in out
