from pydantic import BaseModel, Field, model_validator


def _score(description: str) -> int:
    return Field(ge=0, le=10, description=description)


class _ModelOutput(BaseModel):
    """Base for anything the LLM fills in directly.

    Models occasionally wrap a scalar as {"value": 4} instead of 4. Rejecting
    that ends the session mid-answer, so unwrap it rather than lose the round.
    """

    @model_validator(mode="before")
    @classmethod
    def _unwrap_value_objects(cls, data):
        if not isinstance(data, dict):
            return data
        return {
            key: value["value"]
            if isinstance(value, dict) and set(value) == {"value"}
            else value
            for key, value in data.items()
        }


class ContentScore(_ModelOutput):
    structure: int = _score(
        "0-10. Does the answer give the situation, what the candidate did, and "
        "how it ended, in an order a listener can follow?"
    )
    specificity: int = _score(
        "0-10. Are there concrete details - numbers, timings, named actions - "
        "rather than generalities?"
    )
    ownership: int = _score(
        "0-10. Is it clear what THIS person did, as opposed to what the team did?"
    )


class Evaluation(_ModelOutput):
    content: ContentScore = Field(
        description="How good the answer is as an answer, regardless of its English."
    )
    english: int = _score(
        "0-10. The quality of the English itself - grammar, word choice, fluency. "
        "Required. Score this separately from content: a strong answer in broken "
        "English scores high on content and low here."
    )
    answered_in_english: bool = Field(
        default=True,
        description=(
            "True if the answer is substantially in English and its English can "
            "fairly be scored. False if it is mostly in another language, or "
            "romanized into Latin script from one. Set it to False rather than "
            "scoring the English low: the candidate was invited to answer in "
            "whichever language was easier, and a low score would punish them "
            "for accepting."
        ),
    )
    evidence: list[str] = Field(
        description=(
            "Short exact quotes from the candidate's own answer that justify "
            "the scores. Never paraphrase, never quote words they did not write."
        )
    )

    @property
    def content_total(self) -> int:
        c = self.content
        return round((c.structure + c.specificity + c.ownership) / 3)


class Coaching(_ModelOutput):
    feedback_native: str = Field(
        description=(
            "Two to four sentences of coaching, written in the candidate's own "
            "first language."
        )
    )
    feedback_english: str = Field(
        description=(
            "A faithful English back-translation of feedback_native. Do not "
            "improve or extend it - this exists so the coaching can be checked "
            "by someone who does not read that language."
        )
    )
    model_answer: str = Field(
        description=(
            "The answer in English the candidate could have given, rebuilt from "
            "their own words. Use only facts they actually gave. Where a strong "
            "answer needs a specific they did not supply, write a bracketed "
            "prompt such as [how many days late?] instead of inventing one."
        )
    )


class Round(BaseModel):
    question: str
    first_answer: str
    first_eval: Evaluation
    coaching: Coaching
    retry_answer: str
    retry_eval: Evaluation

    @property
    def content_lift(self) -> int:
        return self.retry_eval.content_total - self.first_eval.content_total

    @property
    def english_lift(self) -> int | None:
        """None when one of the two answers was not in English.

        Subtracting an unscorable English from a scorable one produces a
        number that looks like a verdict and is not one.
        """
        if not (
            self.first_eval.answered_in_english and self.retry_eval.answered_in_english
        ):
            return None
        return self.retry_eval.english - self.first_eval.english


class SessionReport(BaseModel):
    role: str
    language: str
    rounds: list[Round]
    focus_areas: list[str]

    @property
    def average_content_lift(self) -> float:
        average = self._average(lambda r: r.content_lift)
        return 0.0 if average is None else average

    @property
    def average_english_lift(self) -> float | None:
        """None when no round had English on both sides to compare."""
        return self._average(lambda r: r.english_lift)

    def _average(self, lift) -> float | None:
        lifts = [value for value in (lift(r) for r in self.rounds) if value is not None]
        if not lifts:
            return None
        return sum(lifts) / len(lifts)
