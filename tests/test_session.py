import json

import pytest

from coach.models import Coaching, ContentScore, Evaluation, Round
from coach.session import CoachAgents, maybe_save, run_session, unique_path


def _evaluation(score):
    return Evaluation(
        content=ContentScore(structure=score, specificity=score, ownership=score),
        english=score,
        evidence=["quoted"],
    )


class FakeAgents:
    """Records every call and returns scripted results. No network."""

    def __init__(self, scores=None, raise_on_evaluate_call=None):
        self.next_question_calls = []
        self.evaluate_calls = []
        self.coach_calls = []
        self.scores = list(scores or [])
        self.raise_on_evaluate_call = raise_on_evaluate_call

    def as_coach_agents(self):
        return CoachAgents(
            next_question=self.next_question,
            evaluate=self.evaluate,
            coach=self.coach,
        )

    def next_question(self, asked):
        self.next_question_calls.append(list(asked))
        return f"q{len(asked) + 1}"

    def evaluate(self, question, answer):
        self.evaluate_calls.append((question, answer))
        if self.raise_on_evaluate_call == len(self.evaluate_calls):
            raise RuntimeError("ThrottlingException: rate exceeded")
        if self.scores:
            return _evaluation(self.scores.pop(0))
        return _evaluation(5)

    def coach(self, question, answer, evaluation):
        self.coach_calls.append((question, answer, evaluation))
        return Coaching(
            feedback_native="native", feedback_english="english", model_answer="model"
        )


class RecordingObserver:
    def __init__(self):
        self.questions = 0
        self.feedbacks = 0
        self.retries = 0

    def on_question(self, index, total, question):
        self.questions += 1

    def on_feedback(self, evaluation, coaching):
        self.feedbacks += 1

    def on_retry(self, before, after):
        self.retries += 1


def scripted(answers):
    remaining = list(answers)

    def ask(_prompt):
        return remaining.pop(0)

    return ask


def _run(fake, answers, **kwargs):
    return run_session(
        role="Customer support representative",
        experience="Entry level",
        language="Hindi",
        ask=scripted(answers),
        agents=fake.as_coach_agents(),
        **kwargs,
    )


def test_each_question_runs_ask_score_coach_retry_rescore_in_order():
    fake = FakeAgents()
    report = _run(fake, ["a1", "r1", "a2", "r2", "a3", "r3"])
    assert len(report.rounds) == 3
    assert [r.first_answer for r in report.rounds] == ["a1", "a2", "a3"]
    assert [r.retry_answer for r in report.rounds] == ["r1", "r2", "r3"]
    assert len(fake.coach_calls) == 3


def test_retry_is_scored_on_the_same_question_as_the_first_attempt():
    fake = FakeAgents()
    _run(fake, ["a1", "r1", "a2", "r2", "a3", "r3"])
    assert fake.evaluate_calls[0][0] == fake.evaluate_calls[1][0]
    assert fake.evaluate_calls[0][1] == "a1"
    assert fake.evaluate_calls[1][1] == "r1"


def test_the_interviewer_is_told_which_questions_were_already_asked():
    fake = FakeAgents()
    _run(fake, ["a1", "r1", "a2", "r2", "a3", "r3"])
    assert fake.next_question_calls == [[], ["q1"], ["q1", "q2"]]


def test_an_empty_answer_reprompts_and_is_never_evaluated():
    fake = FakeAgents()
    _run(fake, ["", "   ", "a1", "r1", "a2", "r2", "a3", "r3"])
    answers = [answer for _question, answer in fake.evaluate_calls]
    assert "" not in answers
    assert "   " not in answers
    assert answers[0] == "a1"


def test_an_error_mid_session_returns_the_rounds_already_completed():
    fake = FakeAgents(raise_on_evaluate_call=3)
    report = _run(fake, ["a1", "r1", "a2", "r2", "a3", "r3"])
    assert len(report.rounds) == 1
    assert report.rounds[0].first_answer == "a1"


def test_the_observer_is_notified_for_each_question_feedback_and_retry():
    fake = FakeAgents()
    observer = RecordingObserver()
    _run(fake, ["a1", "r1", "a2", "r2", "a3", "r3"], observer=observer)
    assert observer.questions == 3
    assert observer.feedbacks == 3
    assert observer.retries == 3


def test_focus_areas_name_the_weakest_dimensions_of_the_session():
    fake = FakeAgents()
    report = _run(fake, ["a1", "r1", "a2", "r2", "a3", "r3"])
    assert 1 <= len(report.focus_areas) <= 3
    assert all(isinstance(area, str) and area for area in report.focus_areas)


def test_the_retry_prompt_repeats_the_question():
    """By the retry the question has scrolled off behind two feedback panels.
    The demo has to show that the retry really is the same question."""
    prompts = []

    def ask(prompt):
        prompts.append(prompt)
        return "an answer"

    fake = FakeAgents()
    run_session(
        role="Nurse",
        experience="Entry level",
        language="Hindi",
        ask=ask,
        agents=fake.as_coach_agents(),
        questions=1,
    )
    assert "q1" in prompts[1]


def test_unique_path_does_not_overwrite_an_existing_session(tmp_path):
    path = tmp_path / "session.json"
    assert unique_path(path) == path

    path.write_text("first session")
    second = unique_path(path)
    assert second != path
    assert not second.exists()
    assert path.read_text() == "first session"


def test_maybe_save_writes_only_on_an_affirmative_answer(tmp_path):
    fake = FakeAgents()
    report = _run(fake, ["a1", "r1", "a2", "r2", "a3", "r3"])
    path = tmp_path / "session.json"

    assert maybe_save(report, "n", path) is False
    assert not path.exists()

    assert maybe_save(report, "y", path) is True
    assert json.loads(path.read_text())["language"] == "Hindi"


@pytest.mark.parametrize("answer", ["", "no", "nope", "later"])
def test_maybe_save_treats_anything_other_than_yes_as_no(tmp_path, answer):
    fake = FakeAgents()
    report = _run(fake, ["a1", "r1", "a2", "r2", "a3", "r3"])
    path = tmp_path / "session.json"
    assert maybe_save(report, answer, path) is False
    assert not path.exists()


def test_the_retry_prompt_asks_for_english_because_the_interview_will_be_in_english():
    """The first answer may be in any language - that is the point. The retry
    is the rehearsal, so it has to be in the language of the real interview."""
    prompts = []

    def ask(prompt):
        prompts.append(prompt)
        return "an answer"

    fake = FakeAgents()
    run_session(
        role="Nurse",
        experience="Entry level",
        language="Hindi",
        ask=ask,
        agents=fake.as_coach_agents(),
        questions=1,
    )
    assert "English" in prompts[1]


def test_english_is_never_a_focus_area_when_nothing_was_answered_in_english():
    """Telling someone to work on English when they were never scored on it
    is advice drawn from a number that does not exist."""
    from coach.session import FOCUS_ADVICE, focus_areas

    def hindi_eval(score):
        return Evaluation(
            content=ContentScore(
                structure=score, specificity=score, ownership=score
            ),
            english=0,
            answered_in_english=False,
            evidence=["maine suni"],
        )

    rounds = [
        Round(
            question="q",
            first_answer="a",
            first_eval=hindi_eval(score),
            coaching=Coaching(
                feedback_native="x", feedback_english="x", model_answer="x"
            ),
            retry_answer="b",
            retry_eval=hindi_eval(score + 1),
        )
        for score in (2, 3, 4)
    ]

    assert FOCUS_ADVICE["english"] not in focus_areas(rounds)
