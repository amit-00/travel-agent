import json
import os
from datetime import date, timedelta
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch

from wander_agent.state import (
    DaySchedule,
    PlanActivitiesInput,
    ScheduleItem,
    StayWithActivities,
    TripRequest,
)

_SYSTEM_PROMPT = """\
You are a travel activity planner. Given a stay at a location, the accommodation
details, and search results about local attractions, produce a day-by-day
activity schedule.

Rules:
- Check-in day: first activity no earlier than 15:00.
- Check-out day: last activity ends by 11:00, nothing scheduled after.
- Full days: start activities at 09:00, include lunch and dinner restaurant stops.
- Keep activities geographically sensible within a single day.
- Pace the trip appropriately for the trip type and group composition.
- If children are present, prioritise family-friendly activities.

Return a JSON array of day objects covering every date from check_in to
check_out (exclusive):
[
  {
    "date": "YYYY-MM-DD",
    "schedule": [
      {
        "time": "HH:MM",
        "name": "Activity or restaurant name",
        "type": "sightseeing|restaurant|activity|transport|leisure",
        "duration_hours": 2.0,
        "cost_estimate": 20.0,
        "notes": "optional tip"
      }
    ]
  }
]

Return ONLY the JSON array. No markdown, no explanation.\
"""


def build_plan_activities_chain() -> Runnable[dict[str, Any], list[dict[str, Any]]]:
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    search = TavilySearch(
        max_results=5,
        tavily_api_key=os.environ.get("TAVILY_API_KEY", ""),
    )

    async def _invoke(inputs: dict[str, Any]) -> list[dict[str, Any]]:
        stay_with_listings = inputs["stay_with_listings"]
        request: TripRequest = inputs["request"]
        stay = stay_with_listings["stay"]

        query = (
            f"top {request['trip_type']} activities restaurants things to do in "
            f"{stay['location']} for tourists"
        )
        search_results = await search.ainvoke(query)

        accommodation_name = ""
        if stay_with_listings["accommodation_options"]:
            first = stay_with_listings["accommodation_options"][0]
            accommodation_name = str(first.get("title", ""))

        human_content = (
            f"Location: {stay['location']}\n"
            f"Check-in: {stay['check_in']}\n"
            f"Check-out: {stay['check_out']}\n"
            f"Accommodation: {accommodation_name}\n"
            f"Adults: {request['adults']}, Children: {request['children']}\n"
            f"Trip type: {request['trip_type']}\n"
            f"Budget guidance: ${request['budget']} total trip\n\n"
            f"Local search results:\n{search_results}"
        )

        response = await model.ainvoke(
            [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=human_content)]
        )
        raw = str(response.content).strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return list(json.loads(raw))

    return RunnableLambda(_invoke)


def _date_range(check_in: date, check_out: date) -> list[date]:
    days = []
    current = check_in
    while current < check_out:
        days.append(current)
        current += timedelta(days=1)
    return days


async def plan_activities(state: PlanActivitiesInput) -> dict[str, Any]:
    chain = build_plan_activities_chain()
    raw_days = await chain.ainvoke(
        {
            "stay_with_listings": state["stay_with_listings"],
            "request": state["request"],
        }
    )

    stay = state["stay_with_listings"]["stay"]
    expected_dates = _date_range(stay["check_in"], stay["check_out"])
    days_by_date = {
        (d["date"].isoformat() if isinstance(d["date"], date) else d["date"]): d
        for d in raw_days
    }

    days: list[DaySchedule] = []
    for d in expected_dates:
        date_str = d.isoformat()
        raw = days_by_date.get(date_str, {})
        schedule = [
            ScheduleItem(
                time=item.get("time", "09:00"),
                name=item.get("name", ""),
                type=item.get("type", "activity"),
                duration_hours=float(item.get("duration_hours", 1.0)),
                cost_estimate=float(item.get("cost_estimate", 0.0)),
                notes=item.get("notes", ""),
            )
            for item in raw.get("schedule", [])
        ]
        days.append(DaySchedule(date=d, schedule=schedule))

    return {"activity_results": [StayWithActivities(stay=stay, days=days)]}
