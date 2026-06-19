import json
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from wander_agent.graph import graph
from wander_agent.models import ItineraryRequest
from wander_agent.state import TripRequest, WanderState

_NODE_MESSAGES: dict[str, str] = {
    "plan_stays": "Analyzing your destination and planning your stops...",
    "research_stay": "Searching accommodations...",
    "fanout_travel": "Coordinating travel between stays...",
    "plan_travel": "Finding travel options between destinations...",
    "fanout_activities": "Preparing activity planning...",
    "plan_activities": "Planning activities and dining...",
    "compile_itinerary": "Assembling your itinerary...",
}

_INTERNAL_NODES = {"fanout_travel", "fanout_activities"}


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="Wander Agent API", version="0.1.0")


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/itinerary")
async def create_itinerary(request: ItineraryRequest) -> StreamingResponse:
    initial_state = WanderState(
        request=TripRequest(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            adults=request.adults,
            children=request.children,
            budget=request.budget,
            trip_type=request.trip_type,
        ),
        stays=[],
        accommodation_results=[],
        travel_results=[],
        activity_results=[],
        itinerary=None,
    )

    return StreamingResponse(
        _stream_itinerary(initial_state, request.destination),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _stream_itinerary(
    state: WanderState, destination: str
) -> AsyncGenerator[str, None]:
    seen_nodes: set[str] = set()
    itinerary: dict[str, object] | None = None

    try:
        async for event in graph.astream_events(state, version="v2"):
            event_type: str = event.get("event", "")
            node_name: str = event.get("name", "")

            if event_type == "on_chain_start" and node_name in _NODE_MESSAGES:
                if node_name in _INTERNAL_NODES:
                    continue
                message = _NODE_MESSAGES[node_name]
                if node_name == "research_stay":
                    pass
                if node_name not in seen_nodes or node_name == "research_stay":
                    seen_nodes.add(node_name)
                    payload = {
                        "event": "status",
                        "node": node_name,
                        "message": message,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

            elif event_type == "on_chain_end" and node_name == "compile_itinerary":
                output: object = event.get("data", {}).get("output", {})
                if isinstance(output, dict):
                    itinerary = output.get("itinerary")

        if itinerary is not None:
            complete_payload: dict[str, object] = {
                "event": "complete",
                "itinerary": itinerary,
            }
            yield f"data: {json.dumps(complete_payload)}\n\n"
        else:
            payload = {"event": "error", "message": "No itinerary produced"}
            yield f"data: {json.dumps(payload)}\n\n"

    except Exception as exc:
        payload = {"event": "error", "message": str(exc)}
        yield f"data: {json.dumps(payload)}\n\n"
