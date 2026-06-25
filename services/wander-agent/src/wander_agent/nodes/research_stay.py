import logging
from typing import Any

from wander_agent.state import ResearchStayInput, Stay, StayWithListings
from wander_agent.tools.listings import search_listings

logger = logging.getLogger(__name__)


async def research_stay(state: ResearchStayInput) -> dict[str, Any]:
    stay: Stay = state["stay"]
    request = state["request"]

    try:
        options = await search_listings(
            location=stay["location"],
            check_in=stay["check_in"],
            check_out=stay["check_out"],
            adults=request["adults"],
            children=request["children"],
        )
    except Exception:
        logger.exception("Listings service unavailable for %s", stay["location"])
        options = []

    return {
        "accommodation_results": [
            StayWithListings(stay=stay, accommodation_options=options)
        ]
    }
