import operator
from datetime import date
from typing import Annotated

from typing_extensions import TypedDict


class TripRequest(TypedDict):
    destination: str
    start_date: date
    end_date: date
    adults: int
    children: int
    budget: float
    trip_type: str


class Stay(TypedDict):
    location: str
    airport_code: str
    check_in: date
    check_out: date
    rationale: str


class StayWithListings(TypedDict):
    stay: Stay
    accommodation_options: list[dict[str, object]]


class TravelLeg(TypedDict):
    from_location: str
    from_airport: str
    to_location: str
    to_airport: str
    options: list[dict[str, object]]


class ScheduleItem(TypedDict):
    time: str
    name: str
    type: str
    duration_hours: float
    cost_estimate: float
    notes: str


class DaySchedule(TypedDict):
    date: date
    schedule: list[ScheduleItem]


class StayWithActivities(TypedDict):
    stay: Stay
    days: list[DaySchedule]


class WanderState(TypedDict):
    request: TripRequest
    stays: list[Stay]
    accommodation_results: Annotated[list[StayWithListings], operator.add]
    travel_results: Annotated[list[TravelLeg], operator.add]
    activity_results: Annotated[list[StayWithActivities], operator.add]
    itinerary: dict[str, object] | None


# Per-node input TypedDicts used with LangGraph Send API


class ResearchStayInput(TypedDict):
    stay: Stay
    request: TripRequest


class PlanTravelInput(TypedDict):
    from_stay: Stay
    to_stay: Stay
    traveler_count: int


class PlanActivitiesInput(TypedDict):
    stay_with_listings: StayWithListings
    request: TripRequest
