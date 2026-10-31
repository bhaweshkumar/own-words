import pytest
from pydantic import ValidationError

from coach.models import ContentScore, Evaluation, Coaching, Round, SessionReport


def _evaluation(structure, specificity, ownership, english):
    return Evaluation(
        content=ContentScore(
            structure=structure, specificity=specificity, ownership=ownership
        ),
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
        coaching=Coaching(
            feedback_native="...", feedback_english="...", model_answer="..."
        ),
        retry_answer="A customer called about a delivery four days late...",
        retry_eval=_evaluation(8, 8, 8, 7),
    )
    assert r.content_lift == 4
    assert r.english_lift == 2


def test_negative_lift_is_reported_as_negative():
    r = Round(
        question="q",
        first_answer="a",
        first_eval=_evaluation(8, 8, 8, 8),
        coaching=Coaching(
            feedback_native="...", feedback_english="...", model_answer="..."
        ),
        retry_answer="b",
        retry_eval=_evaluation(4, 4, 4, 5),
    )
    assert r.content_lift == -4
    assert r.english_lift == -3


def test_average_lifts_over_a_session():
    def rnd(before, after):
        return Round(
            question="q",
            first_answer="a",
            first_eval=_evaluation(before, before, before, before),
            coaching=Coaching(
                feedback_native="x", feedback_english="x", model_answer="x"
            ),
            retry_answer="b",
            retry_eval=_evaluation(after, after, after, after),
        )

    report = SessionReport(
        role="Customer support representative",
        language="Hindi",
        rounds=[rnd(4, 8), rnd(5, 7), rnd(6, 8)],
        focus_areas=[
            "Use the STAR structure",
            "Give one concrete number",
            "Say what you learned",
        ],
    )
    # lifts are 4, 2 and 2
    assert report.average_content_lift == pytest.approx(8 / 3)
    assert report.average_english_lift == pytest.approx(8 / 3)


def test_scores_outside_zero_to_ten_are_rejected():
    with pytest.raises(ValidationError):
        ContentScore(structure=11, specificity=5, ownership=5)


def test_a_score_wrapped_in_a_value_object_is_unwrapped():
    """Observed live: the model sometimes returns {"value": 4} for an integer
    field, which ends the session mid-recording."""
    evaluation = Evaluation.model_validate(
        {
            "content": {
                "structure": {"value": 4},
                "specificity": 3,
                "ownership": {"value": 6},
            },
            "english": {"value": 5},
            "evidence": ["I said sorry"],
        }
    )
    assert evaluation.content.structure == 4
    assert evaluation.content.ownership == 6
    assert evaluation.english == 5


def test_coaching_text_wrapped_in_a_value_object_is_unwrapped():
    coaching = Coaching.model_validate(
        {
            "feedback_native": {"value": "आपका उत्तर छोटा है"},
            "feedback_english": "Your answer is short",
            "model_answer": "[what happened?]",
        }
    )
    assert coaching.feedback_native == "आपका उत्तर छोटा है"


def test_every_scored_field_describes_itself_in_the_json_schema():
    """The schema is the contract the model fills in. An undescribed field
    is one the model silently omits."""
    for model, fields in [
        (ContentScore, ["structure", "specificity", "ownership"]),
        (Evaluation, ["content", "english", "evidence"]),
        (Coaching, ["feedback_native", "feedback_english", "model_answer"]),
    ]:
        properties = model.model_json_schema()["properties"]
        for field in fields:
            assert properties[field].get("description"), (
                f"{model.__name__}.{field} has no description"
            )


def _hindi_evaluation(structure, specificity, ownership):
    """An answer written in Hindi. There is no English in it to score."""
    return Evaluation(
        content=ContentScore(
            structure=structure, specificity=specificity, ownership=ownership
        ),
        english=0,
        answered_in_english=False,
        evidence=["maine unki baat suni"],
    )


def test_english_lift_is_withheld_when_an_answer_was_not_in_english():
    """Observed live: a retry written in Hindi scored English 0, so a session
    that genuinely improved reported english -3.0. The tool invites answers in
    the user's own language; it must not then score them as failed English."""
    r = Round(
        question="q",
        first_answer="customer gussa tha, I said sorry",
        first_eval=_evaluation(2, 2, 2, 6),
        coaching=Coaching(
            feedback_native="...", feedback_english="...", model_answer="..."
        ),
        retry_answer="Maine pehle unki poori baat suni, phir apology ki.",
        retry_eval=_hindi_evaluation(8, 8, 8),
    )
    assert r.content_lift == 6
    assert r.english_lift is None


def test_average_english_lift_ignores_the_rounds_it_could_not_compare():
    def english_round(before, after):
        return Round(
            question="q",
            first_answer="a",
            first_eval=_evaluation(before, before, before, before),
            coaching=Coaching(
                feedback_native="x", feedback_english="x", model_answer="x"
            ),
            retry_answer="b",
            retry_eval=_evaluation(after, after, after, after),
        )

    hindi_round = Round(
        question="q",
        first_answer="a",
        first_eval=_evaluation(2, 2, 2, 6),
        coaching=Coaching(feedback_native="x", feedback_english="x", model_answer="x"),
        retry_answer="b",
        retry_eval=_hindi_evaluation(8, 8, 8),
    )

    report = SessionReport(
        role="Customer support representative",
        language="Hindi",
        rounds=[english_round(4, 8), hindi_round, english_round(5, 7)],
        focus_areas=["Give one concrete number"],
    )
    # English lifts are 4 and 2; the Hindi round contributes nothing.
    assert report.average_english_lift == pytest.approx(3.0)
    # Content is comparable in all three rounds: 4, 6 and 2.
    assert report.average_content_lift == pytest.approx(4.0)


def test_average_english_lift_is_none_when_no_round_can_be_compared():
    report = SessionReport(
        role="Customer support representative",
        language="Hindi",
        rounds=[
            Round(
                question="q",
                first_answer="a",
                first_eval=_hindi_evaluation(2, 2, 2),
                coaching=Coaching(
                    feedback_native="x", feedback_english="x", model_answer="x"
                ),
                retry_answer="b",
                retry_eval=_hindi_evaluation(8, 8, 8),
            )
        ],
        focus_areas=[],
    )
    assert report.average_english_lift is None


def test_whether_the_answer_was_in_english_describes_itself_in_the_json_schema():
    properties = Evaluation.model_json_schema()["properties"]
    assert properties["answered_in_english"].get("description")
