import pytest

from coach.agents import (
    bedrock_model,
    coach_prompt,
    evaluator_prompt,
    interviewer_prompt,
)


def test_bedrock_model_requires_an_explicit_model_id(monkeypatch):
    monkeypatch.delenv("COACH_MODEL_ID", raising=False)
    with pytest.raises(RuntimeError) as exc:
        bedrock_model()
    assert "COACH_MODEL_ID" in str(exc.value)


def test_coach_prompt_names_the_users_language():
    assert "Hindi" in coach_prompt("Hindi")


def test_coach_prompt_forbids_inventing_facts_and_requires_brackets():
    prompt = coach_prompt("Hindi").lower()
    assert "only facts" in prompt or "never invent" in prompt
    assert "[" in prompt


def test_coach_prompt_requires_an_english_back_translation():
    assert "back-translation" in coach_prompt("Hindi").lower()


def test_evaluator_prompt_requires_quoting_the_answer_as_evidence():
    assert "quote" in evaluator_prompt().lower()


def test_evaluator_prompt_scores_english_separately_from_content():
    prompt = evaluator_prompt().lower()
    assert "english" in prompt
    assert "never" in prompt and "blend" in prompt


def test_live_agents_silence_the_sdk_so_it_cannot_print_over_the_interface(monkeypatch):
    """Strands agents stream to stdout by default, which duplicates every
    question and leaks 'Tool #1: Evaluation' into the session display."""
    import coach.agents as agents_module

    recorded = []

    class SpyAgent:
        def __init__(self, **kwargs):
            recorded.append(kwargs)

        def __call__(self, _prompt):
            return "a question"

    monkeypatch.setattr(agents_module, "Agent", SpyAgent)
    monkeypatch.setattr(agents_module, "bedrock_model", lambda: object())

    agents_module.live_agents("Nurse", "Entry level", "Hindi").next_question([])

    assert recorded, "no agent was constructed"
    for kwargs in recorded:
        assert "callback_handler" in kwargs
        assert kwargs["callback_handler"] is None


def test_every_evaluation_gets_a_fresh_agent_so_the_retry_cannot_be_anchored(
    monkeypatch,
):
    """The whole before/after claim rests on this. A reused evaluator would
    carry history and score the retry while remembering the first attempt."""
    import coach.agents as agents_module

    constructed = []

    class SpyAgent:
        def __init__(self, **kwargs):
            constructed.append(kwargs)

        def structured_output(self, _model, _prompt):
            return None

    monkeypatch.setattr(agents_module, "Agent", SpyAgent)
    monkeypatch.setattr(agents_module, "bedrock_model", lambda: object())

    agents = agents_module.live_agents("Nurse", "Entry level", "Hindi")
    agents.evaluate("q1", "first attempt")
    agents.evaluate("q1", "the retry")

    assert len(constructed) == 2, "the evaluator agent was reused across attempts"
    assert all("messages" not in kwargs for kwargs in constructed)


def test_the_public_agent_builders_also_silence_the_sdk(monkeypatch):
    """They must not diverge from live_agents and reintroduce the stdout leak."""
    import coach.agents as agents_module

    constructed = []

    class SpyAgent:
        def __init__(self, **kwargs):
            constructed.append(kwargs)

    monkeypatch.setattr(agents_module, "Agent", SpyAgent)
    monkeypatch.setattr(agents_module, "bedrock_model", lambda: object())

    agents_module.build_interviewer("Nurse", "Entry level")
    agents_module.build_evaluator()
    agents_module.build_coach("Hindi")

    assert len(constructed) == 3
    for kwargs in constructed:
        assert kwargs.get("callback_handler", "missing") is None


def test_interviewer_prompt_holds_difficulty_flat_and_names_the_role():
    prompt = interviewer_prompt("Customer support representative", "Entry level")
    assert "Customer support representative" in prompt
    assert "Entry level" in prompt
    assert "difficulty" in prompt.lower()
