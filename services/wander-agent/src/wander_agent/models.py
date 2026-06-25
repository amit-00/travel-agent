from datetime import date

from pydantic import BaseModel, Field, model_validator


class ItineraryRequest(BaseModel):
    destination: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date
    adults: int = Field(ge=1)
    children: int = Field(ge=0, default=0)
    budget: float = Field(gt=0)
    trip_type: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def end_after_start(self) -> "ItineraryRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class SseEvent(BaseModel):
    event: str
    node: str | None = None
    message: str | None = None
    itinerary: dict[str, object] | None = None
