from datetime import datetime

from pydantic import BaseModel, Field


class Layover(BaseModel):
    airport: str
    duration_minutes: int = Field(gt=0)


class FlightOption(BaseModel):
    airline: str
    departure_datetime: datetime
    arrival_datetime: datetime
    cost_per_ticket: float = Field(gt=0)
    layovers: list[Layover]


class FlightsPayload(BaseModel):
    options: list[FlightOption] = Field(min_length=3, max_length=3)


class FlightsResponse(BaseModel):
    departure_airport: str
    arrival_airport: str
    traveler_count: int
    options: list[FlightOption]
