import os

from pydantic import ValidationError
from strands import Agent
from strands.models import BedrockModel

from coach.models import Coaching, Evaluation
from coach.session import CoachAgents

DISCOVERY_HINT = (
    "Set COACH_MODEL_ID to a Bedrock model or inference profile your account "
    "can invoke. List what is available with:\n"
    "  aws bedrock list-inference-profiles --region $AWS_REGION"
)


def bedrock_model() -> BedrockModel:
    model_id = os.environ.get("COACH_MODEL_ID", "").strip()
    if not model_id:
        raise RuntimeError(f"COACH_MODEL_ID is not set.\n{DISCOVERY_HINT}")
    return BedrockModel(
        model_id=model_id, region_name=os.environ.get("AWS_REGION", "us-east-1")
    )


def interviewer_prompt(role: str, experience: str) -> str:
    return f"""You are interviewing a candidate for this role: {role}
Their experience level is: {experience}

Ask exactly one interview question. Output only the question itself, with no
preamble, numbering or commentary.

Rules:
- Ask the kind of question a real hiring manager for this role would ask.
- Never repeat a theme already covered by an earlier question in this session.
- Hold the difficulty flat across the session. Every question must be about as
  hard as the first one, because the candidate's scores are compared across
  questions and a harder question would make a real improvement look like a
  decline.
- Keep the question under 40 words and in plain English. The candidate may not
  be a native speaker."""


def evaluator_prompt() -> str:
    return """You score a candidate's answer to a mock interview question.

Score each of these from 0 to 10:
- structure: does the answer set out the situation, what they did, and how it
  ended, in an order a listener can follow?
- specificity: are there concrete details, numbers, names of actions taken?
- ownership: is it clear what THIS person did, rather than what "we" did?
- english: the quality of the English itself - grammar, word choice, fluency.

The first three are content. English is scored separately and must never be
blended into the content scores. A brilliant answer in broken English scores
high on content and low on english. A fluent answer with nothing in it scores
the other way round. Keeping them apart is the entire point: it tells the
candidate which problem they actually have.

Also set `answered_in_english`. It is true when the answer is substantially in
English. It is false when the answer is mostly in another language, including
one romanized into Latin script - "maine unki baat suni" is Hindi, not weak
English. Score content as normal either way; the substance is still there to
judge. But when it is false, set english to 0 and understand that the number
will be discarded rather than shown. Never score the English of an answer that
was not written in English: the candidate was told to answer in whichever
language was easier, and scoring them down for it punishes them for believing
us.

Score the answer on its substance, not its length or polish.

In `evidence`, quote the candidate's own words - short, exact phrases from
their answer - to justify the scores. Never paraphrase in evidence, and never
quote words they did not write.

Apply the same rubric whether this is a first attempt or a second attempt at
the same question."""


def coach_prompt(language: str) -> str:
    return f"""You coach a candidate who is preparing for job interviews in
English. Their first language is {language}. They may be stronger in
{language} than in English, and may have answered in a mix of both.

Produce three things.

1. feedback_native: your coaching, written in {language}. Be specific and
   kind. Tell them what was missing and what to do differently next time. If
   {language} is English, write it in plain English. Two to four sentences.

2. feedback_english: a faithful English back-translation of exactly what you
   wrote in feedback_native. Do not improve it, extend it or soften it in
   translation - this exists so the coaching can be checked by someone who
   does not read {language}. If feedback_native is already English, repeat it
   unchanged.

3. model_answer: the answer in English that this candidate could have given,
   rebuilt from their own answer.

The rule for model_answer, which you must never break: use only facts the
candidate actually gave you. Never invent a number, a date, a job title, a
company, an outcome or an action they did not mention. Where a strong answer
would need a specific they did not supply, write a bracketed prompt in its
place, like [how many days late?] or [what did you check first?], so they can
fill it in themselves.

This matters because they may memorize this answer and say it in a real
interview. A detail you invented would become a lie told on their behalf, and
they would be caught telling it. A model answer that is mostly brackets is a
correct result, not a failure."""


def retry_once(call):
    """Structured output occasionally comes back malformed. A session is
    recorded in one take, so pay for a second call rather than lose the round."""
    try:
        return call()
    except ValidationError:
        return call()


def _agent(model, system_prompt: str) -> Agent:
    # callback_handler=None stops the SDK streaming its own output over the
    # session display. Every agent in this module goes through here so no
    # builder can quietly reintroduce that.
    return Agent(model=model, system_prompt=system_prompt, callback_handler=None)


def build_interviewer(role: str, experience: str) -> Agent:
    return _agent(bedrock_model(), interviewer_prompt(role, experience))


def build_evaluator() -> Agent:
    return _agent(bedrock_model(), evaluator_prompt())


def build_coach(language: str) -> Agent:
    return _agent(bedrock_model(), coach_prompt(language))


def live_agents(role: str, experience: str, language: str) -> CoachAgents:
    model = bedrock_model()

    def agent(system_prompt: str) -> Agent:
        # A fresh agent per call: an evaluator that remembered the first
        # attempt would score the retry against it, and the before/after
        # number is the whole claim.
        return _agent(model, system_prompt)

    def next_question(asked: list[str]) -> str:
        if asked:
            already = "\n".join(f"- {q}" for q in asked)
            prompt = f"Questions already asked:\n{already}\n\nAsk the next one."
        else:
            prompt = "Ask the first question."
        return str(agent(interviewer_prompt(role, experience))(prompt)).strip()

    def evaluate(question: str, answer: str) -> Evaluation:
        return retry_once(
            lambda: agent(evaluator_prompt()).structured_output(
                Evaluation,
                f"Interview question:\n{question}\n\nCandidate's answer:\n{answer}",
            )
        )

    def coach(question: str, answer: str, evaluation: Evaluation) -> Coaching:
        return retry_once(
            lambda: agent(coach_prompt(language)).structured_output(
                Coaching,
                f"Interview question:\n{question}\n\n"
                f"Candidate's answer:\n{answer}\n\n"
                f"Scores - structure {evaluation.content.structure}, "
                f"specificity {evaluation.content.specificity}, "
                f"ownership {evaluation.content.ownership}, "
                f"english {evaluation.english}.\n"
                f"Evidence quoted by the scorer: {evaluation.evidence}",
            )
        )

    return CoachAgents(next_question=next_question, evaluate=evaluate, coach=coach)
