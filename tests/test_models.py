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
