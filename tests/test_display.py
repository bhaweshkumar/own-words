from rich.console import Console

from coach.display import (
    ConsoleObserver,
    render_feedback,
    render_question,
    render_report,
    render_retry,
)
from coach.models import Coaching, ContentScore, Evaluation, Round, SessionReport


def _console():
    return Console(record=True, width=80, force_terminal=False)


def _evaluation(structure, specificity, ownership, english):
    return Evaluation(
        content=ContentScore(
            structure=structure, specificity=specificity, ownership=ownership
        ),
        english=english,
        evidence=["I said sorry"],
    )


def _coaching(native="native feedback", english="english feedback", answer="model"):
    return Coaching(
        feedback_native=native, feedback_english=english, model_answer=answer
    )


def _render(fn, *args):
    console = _console()
    fn(console, *args)
    return console.export_text()


def _round(before, after):
    return Round(
        question="Tell me about a difficult customer.",
        first_answer="a",
        first_eval=_evaluation(before, before, before, before),
        coaching=_coaching(),
        retry_answer="b",
        retry_eval=_evaluation(after, after, after, after),
    )


def test_feedback_shows_content_and_english_as_separate_scores():
    text = _render(render_feedback, _evaluation(2, 3, 6, 5), _coaching())
    assert "Content 4/10" in text
    assert "English 5/10" in text


def test_feedback_shows_the_native_text_and_its_english_back_translation():
    text = _render(
        render_feedback,
        _evaluation(2, 3, 6, 5),
        _coaching(native="आपने जो किया वह सही था", english="What you did was right"),
    )
    assert "आपने जो किया वह सही था" in text
    assert "What you did was right" in text


def test_feedback_shows_the_model_answer_even_when_it_is_only_brackets():
    text = _render(
        render_feedback,
        _evaluation(1, 1, 1, 2),
        _coaching(answer="[what was the situation?]"),
    )
    assert "[what was the situation?]" in text


def test_retry_result_shows_the_before_and_after_on_both_axes():
    text = _render(render_retry, _evaluation(2, 3, 6, 5), _evaluation(8, 8, 8, 7))
    assert "4 → 8" in text
    assert "5 → 7" in text


def test_feedback_quotes_the_candidates_own_words_back():
    """Spec anti-goal: generic praise. The critique has to show what in their
    own answer earned the score."""
    evaluation = Evaluation(
        content=ContentScore(structure=2, specificity=3, ownership=6),
        english=5,
        evidence=["customer bahut gussa tha", "I said sorry"],
    )
    text = _render(render_feedback, evaluation, _coaching())
    assert "customer bahut gussa tha" in text
    assert "I said sorry" in text


def test_retry_result_marks_a_genuine_improvement():
    text = _render(render_retry, _evaluation(2, 3, 6, 5), _evaluation(8, 8, 8, 7))
    assert "improved" in text.lower()


def test_retry_result_does_not_congratulate_a_score_that_fell():
    text = _render(render_retry, _evaluation(8, 8, 8, 8), _evaluation(4, 4, 4, 4))
    assert "8 → 4" in text
    assert "improved" not in text.lower()


def test_question_shows_its_position_in_the_session():
    text = _render(render_question, 2, 3, "Tell me about a difficult customer.")
    assert "2" in text and "3" in text
    assert "Tell me about a difficult customer." in text


def test_report_shows_per_question_rows_and_average_lift():
    report = SessionReport(
        role="Customer support representative",
        language="Hindi",
        rounds=[_round(4, 8), _round(5, 7), _round(6, 8)],
        focus_areas=["Use the STAR structure"],
    )
    text = _render(render_report, report)
    assert "Average lift" in text
    assert "Use the STAR structure" in text


def test_devanagari_renders_without_a_unicode_error():
    report = SessionReport(
        role="नर्स",
        language="Hindi",
        rounds=[_round(4, 8)],
        focus_areas=["हर जवाब में एक ठोस संख्या दीजिए"],
    )
    text = _render(render_report, report)
    assert "हर जवाब में एक ठोस संख्या दीजिए" in text


def test_the_console_observer_satisfies_the_session_observer_protocol():
    observer = ConsoleObserver(_console())
    for method in ("on_question", "on_feedback", "on_retry", "on_error"):
        assert callable(getattr(observer, method))


def _hindi_evaluation(score):
    return Evaluation(
        content=ContentScore(structure=score, specificity=score, ownership=score),
        english=0,
        answered_in_english=False,
        evidence=["maine unki baat suni"],
    )


def test_an_english_score_that_could_not_be_compared_is_not_shown_as_a_number():
    """A Hindi retry scored English 0 reads as a collapse. It is an absence."""
    text = _render(render_retry, _evaluation(2, 2, 2, 6), _hindi_evaluation(8))
    assert "2 → 8" in text
    assert "6 → 0" not in text
    assert "not scored" in text.lower()


def test_the_improvement_mark_is_withheld_when_the_other_axis_fell():
    """Content up, English down is not 'you improved this answer' - it is a
    trade, and the user has to see which way."""
    text = _render(render_retry, _evaluation(2, 2, 2, 8), _evaluation(8, 8, 8, 3))
    assert "improved" not in text.lower()


def test_the_improvement_mark_still_appears_when_english_was_not_comparable():
    text = _render(render_retry, _evaluation(2, 2, 2, 6), _hindi_evaluation(8))
    assert "improved" in text.lower()


def test_the_report_leaves_the_english_column_blank_for_a_round_it_could_not_compare():
    hindi_round = Round(
        question="Tell me about a difficult customer.",
        first_answer="a",
        first_eval=_evaluation(2, 2, 2, 6),
        coaching=_coaching(),
        retry_answer="b",
        retry_eval=_hindi_evaluation(8),
    )
    report = SessionReport(
        role="Customer support representative",
        language="Hindi",
        rounds=[hindi_round],
        focus_areas=["Give one concrete number"],
    )
    text = _render(render_report, report)
    assert "2 → 8" in text
    assert "6 → 0" not in text


def test_the_report_omits_the_average_english_lift_when_there_is_none_to_report():
    hindi_round = Round(
        question="q",
        first_answer="a",
        first_eval=_hindi_evaluation(2),
        coaching=_coaching(),
        retry_answer="b",
        retry_eval=_hindi_evaluation(8),
    )
    report = SessionReport(
        role="Customer support representative",
        language="Hindi",
        rounds=[hindi_round],
        focus_areas=[],
    )
    text = _render(render_report, report)
    assert "content +6.0" in text
    assert "english" not in text.lower().split("content")[-1]


def test_the_feedback_panel_does_not_show_an_english_score_for_a_non_english_answer():
    """The candidate was invited to answer in their own language. 'English 0/10'
    on that answer reads as a failure the tool itself encouraged."""
    text = _render(render_feedback, _hindi_evaluation(5), _coaching())
    assert "English 0/10" not in text
    assert "English —" in text
    assert "not in English" in text


def test_the_feedback_panel_still_shows_the_english_score_for_an_english_answer():
    text = _render(render_feedback, _evaluation(5, 5, 5, 7), _coaching())
    assert "English 7/10" in text
