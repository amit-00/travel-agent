from typing import Any, cast

from wander_agent.state import (
    StayWithActivities,
    StayWithListings,
    TravelLeg,
    WanderState,
)


def _estimate_cost(
    accommodation_results: list[StayWithListings],
    travel_results: list[TravelLeg],
    activity_results: list[StayWithActivities],
    adults: int,
    children: int,
) -> float:
    total = 0.0
    traveler_count = adults + children

    for entry in accommodation_results:
        stay = entry["stay"]
        nights = (stay["check_out"] - stay["check_in"]).days
        options = entry["accommodation_options"]
        if options:
            price = cast(float, options[0].get("price_per_night", 0.0))
            total += float(price) * nights

    for leg in travel_results:
        if leg["options"]:
            cost_per_ticket = cast(float, leg["options"][0].get("cost_per_ticket", 0.0))
            total += float(cost_per_ticket) * traveler_count

    for activity_entry in activity_results:
        for day in activity_entry["days"]:
            for item in day["schedule"]:
                total += item["cost_estimate"] * traveler_count

    return round(total, 2)


async def compile_itinerary(state: WanderState) -> dict[str, Any]:
    request = state["request"]
    stays = state["stays"]
    accommodation_results = state["accommodation_results"]
    travel_results = state["travel_results"]
    activity_results = state["activity_results"]

    estimated_cost = _estimate_cost(
        accommodation_results,
        travel_results,
        activity_results,
        request["adults"],
        request["children"],
    )

    budget_warning: str | None = None
    if estimated_cost > request["budget"]:
        budget_warning = (
            f"Estimated cost of ${estimated_cost:,.2f} exceeds your budget of "
            f"${request['budget']:,.2f}"
        )

    acc_by_location = {e["stay"]["location"]: e for e in accommodation_results}
    travel_by_from = {leg["from_location"]: leg for leg in travel_results}
    activities_by_location = {e["stay"]["location"]: e for e in activity_results}

    compiled_stays: list[dict[str, Any]] = []
    for i, stay in enumerate(stays):
        location = stay["location"]
        acc = acc_by_location.get(location)
        activities = activities_by_location.get(location)

        is_last = i == len(stays) - 1
        travel_to_next: dict[str, Any] | None = None
        if not is_last:
            leg = travel_by_from.get(location)
            if leg:
                travel_to_next = {
                    "destination": leg["to_location"],
                    "options": leg["options"],
                }

        nights = (stay["check_out"] - stay["check_in"]).days
        compiled_stays.append(
            {
                "location": location,
                "check_in": stay["check_in"].isoformat(),
                "check_out": stay["check_out"].isoformat(),
                "nights": nights,
                "rationale": stay["rationale"],
                "accommodation_options": acc["accommodation_options"] if acc else [],
                "travel_to_next": travel_to_next,
                "days": [
                    {
                        "date": day["date"].isoformat(),
                        "schedule": list(day["schedule"]),
                    }
                    for day in (activities["days"] if activities else [])
                ],
            }
        )

    total_nights = (request["end_date"] - request["start_date"]).days
    itinerary: dict[str, Any] = {
        "destination": request["destination"],
        "trip_type": request["trip_type"],
        "total_nights": total_nights,
        "group": {"adults": request["adults"], "children": request["children"]},
        "budget": request["budget"],
        "estimated_cost": estimated_cost,
        "budget_warning": budget_warning,
        "stays": compiled_stays,
    }

    return {"itinerary": itinerary}
