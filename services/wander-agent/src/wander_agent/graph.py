from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from wander_agent.nodes.compile_itinerary import compile_itinerary
from wander_agent.nodes.plan_activities import plan_activities
from wander_agent.nodes.plan_stays import plan_stays
from wander_agent.nodes.plan_travel import plan_travel
from wander_agent.nodes.research_stay import research_stay
from wander_agent.state import (
    PlanActivitiesInput,
    PlanTravelInput,
    ResearchStayInput,
    WanderState,
)


def _route_to_research(state: WanderState) -> list[Send]:
    return [
        Send("research_stay", ResearchStayInput(stay=stay, request=state["request"]))
        for stay in state["stays"]
    ]


def _fanout_travel(state: WanderState) -> dict[str, Any]:
    """Barrier node: runs once after ALL research_stay instances complete."""
    return {}


def _route_from_fanout_travel(state: WanderState) -> list[Send] | str:
    stays = state["stays"]
    if len(stays) < 2:
        return "fanout_activities"
    traveler_count = state["request"]["adults"] + state["request"]["children"]
    return [
        Send(
            "plan_travel",
            PlanTravelInput(
                from_stay=stays[i],
                to_stay=stays[i + 1],
                traveler_count=traveler_count,
            ),
        )
        for i in range(len(stays) - 1)
    ]


def _fanout_activities(state: WanderState) -> dict[str, Any]:
    """Barrier node: runs once after ALL plan_travel instances complete."""
    return {}


def _route_to_activities(state: WanderState) -> list[Send]:
    acc_by_location = {e["stay"]["location"]: e for e in state["accommodation_results"]}
    return [
        Send(
            "plan_activities",
            PlanActivitiesInput(
                stay_with_listings=acc_by_location.get(
                    stay["location"],
                    {"stay": stay, "accommodation_options": []},
                ),
                request=state["request"],
            ),
        )
        for stay in state["stays"]
    ]


builder: StateGraph[WanderState] = StateGraph(WanderState)

builder.add_node("plan_stays", plan_stays)
builder.add_node("research_stay", research_stay)
builder.add_node("fanout_travel", _fanout_travel)
builder.add_node("plan_travel", plan_travel)
builder.add_node("fanout_activities", _fanout_activities)
builder.add_node("plan_activities", plan_activities)
builder.add_node("compile_itinerary", compile_itinerary)

builder.set_entry_point("plan_stays")
builder.add_conditional_edges("plan_stays", _route_to_research, ["research_stay"])
builder.add_edge("research_stay", "fanout_travel")
builder.add_conditional_edges(
    "fanout_travel",
    _route_from_fanout_travel,
    ["plan_travel", "fanout_activities"],
)
builder.add_edge("plan_travel", "fanout_activities")
builder.add_conditional_edges(
    "fanout_activities", _route_to_activities, ["plan_activities"]
)
builder.add_edge("plan_activities", "compile_itinerary")
builder.add_edge("compile_itinerary", END)

graph = builder.compile()
