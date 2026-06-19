import json
import os
from datetime import date
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch

from wander_agent.state import Stay, TripRequest, WanderState

_SYSTEM_PROMPT = """\
You are an expert travel planner. Given a trip request, determine the optimal
sub-destinations (stays) the traveller should make. Each stay is a distinct
location where they'll spend 1 or more nights at a single accommodation.

Rules:
- If the destination is granular enough (e.g. a single city), return just 1 stay.
- Order stays geographically to minimise backtracking.
- Allocate nights proportionally based on attractions and the trip type.
- Include the nearest major international airport IATA code for each stay.
- Use the provided search results to inform your decisions.

Return a JSON array of stay objects with these exact fields:
[
  {
    "location": "City Name",
    "airport_code": "XXX",
    "check_in": "YYYY-MM-DD",
    "check_out": "YYYY-MM-DD",
    "rationale": "Why this stop fits the trip"
  }
]

Return ONLY the JSON array. No markdown, no explanation.\
"""


def build_plan_stays_chain() -> Runnable[dict[str, Any], list[Stay]]:
    model = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
    search = TavilySearch(
        max_results=5,
        tavily_api_key=os.environ.get("TAVILY_API_KEY", ""),
    )

    async def _invoke(inputs: dict[str, Any]) -> list[Stay]:
        request: TripRequest = inputs["request"]
        query = (
            f"best places to visit in {request['destination']} "
            f"for {request['trip_type']} travel "
            f"{request['adults']} adults {request['children']} children"
        )
        search_results = await search.ainvoke(query)

        human_content = (
            f"Destination: {request['destination']}\n"
            f"Start date: {request['start_date']}\n"
            f"End date: {request['end_date']}\n"
            f"Adults: {request['adults']}, Children: {request['children']}\n"
            f"Budget: ${request['budget']}\n"
            f"Trip type: {request['trip_type']}\n\n"
            f"Search results:\n{search_results}"
        )

        response = await model.ainvoke(
            [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=human_content)]
        )
        raw = str(response.content).strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data: list[dict[str, Any]] = json.loads(raw)
        return [
            Stay(
                location=item["location"],
                airport_code=item["airport_code"],
                check_in=date.fromisoformat(item["check_in"]),
                check_out=date.fromisoformat(item["check_out"]),
                rationale=item.get("rationale", ""),
            )
            for item in data
        ]

    from langchain_core.runnables import RunnableLambda

    return RunnableLambda(_invoke)


async def plan_stays(state: WanderState) -> dict[str, Any]:
    chain = build_plan_stays_chain()
    stays = await chain.ainvoke({"request": state["request"]})
    return {"stays": stays}
