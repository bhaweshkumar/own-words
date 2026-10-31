from pydantic import BaseModel, Field

Score = Field(ge=0, le=10)


class ContentScore(BaseModel):
    structure: int = Score
    specificity: int = Score
    ownership: int = Score


class Evaluation(BaseModel):
    content: ContentScore
    english: int = Score
    evidence: list[str]

    @property
    def content_total(self) -> int:
        c = self.content
        return round((c.structure + c.specificity + c.ownership) / 3)


class Coaching(BaseModel):
    feedback_native: str
    feedback_english: str
    model_answer: str


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
    def english_lift(self) -> int:
        return self.retry_eval.english - self.first_eval.english


class SessionReport(BaseModel):
    role: str
    language: str
    rounds: list[Round]
    focus_areas: list[str]

    @property
    def average_content_lift(self) -> float:
        return self._average(lambda r: r.content_lift)

    @property
    def average_english_lift(self) -> float:
        return self._average(lambda r: r.english_lift)

    def _average(self, lift) -> float:
        if not self.rounds:
            return 0.0
        return sum(lift(r) for r in self.rounds) / len(self.rounds)
