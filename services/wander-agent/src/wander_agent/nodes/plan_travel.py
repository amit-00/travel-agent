import logging
from typing import Any

from wander_agent.state import PlanTravelInput, Stay, TravelLeg
from wander_agent.tools.travel import search_flights

logger = logging.getLogger(__name__)


async def plan_travel(state: PlanTravelInput) -> dict[str, Any]:
    from_stay: Stay = state["from_stay"]
    to_stay: Stay = state["to_stay"]
    traveler_count: int = state["traveler_count"]

    departure_datetime = f"{from_stay['check_out'].isoformat()}T10:00:00"

    try:
        options = await search_flights(
            departure_airport=from_stay["airport_code"],
            arrival_airport=to_stay["airport_code"],
            traveler_count=traveler_count,
            departure_datetime=departure_datetime,
        )
    except Exception:
        logger.exception(
            "Travel service unavailable for %s → %s",
            from_stay["location"],
            to_stay["location"],
        )
        options = []

    return {
        "travel_results": [
            TravelLeg(
                from_location=from_stay["location"],
                from_airport=from_stay["airport_code"],
                to_location=to_stay["location"],
                to_airport=to_stay["airport_code"],
                options=options,
            )
        ]
    }
