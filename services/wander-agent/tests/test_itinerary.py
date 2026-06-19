import json
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient


def _make_itinerary() -> dict[str, Any]:
    return {
        "destination": "Italy",
        "trip_type": "sightseeing",
        "total_nights": 10,
        "group": {"adults": 2, "children": 0},
        "budget": 5000.0,
        "estimated_cost": 4200.0,
        "budget_warning": None,
        "stays": [
            {
                "location": "Rome",
                "check_in": "2025-07-01",
                "check_out": "2025-07-04",
                "nights": 3,
                "rationale": "Iconic city",
                "accommodation_options": [],
                "travel_to_next": None,
                "days": [],
            }
        ],
    }


async def _mock_stream(
    state: dict[str, Any], **kwargs: Any
) -> AsyncGenerator[dict[str, Any], None]:
    yield {"event": "on_chain_start", "name": "plan_stays", "data": {}}
    yield {"event": "on_chain_start", "name": "research_stay", "data": {}}
    yield {"event": "on_chain_start", "name": "compile_itinerary", "data": {}}
    yield {
        "event": "on_chain_end",
        "name": "compile_itinerary",
        "data": {"output": {"itinerary": _make_itinerary()}},
    }


def test_health_unchanged() -> None:
    from wander_agent.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_itinerary_invalid_request_returns_422() -> None:
    from wander_agent.main import app

    client = TestClient(app)
    response = client.post(
        "/itinerary",
        json={
            "destination": "Italy",
            "start_date": "2025-07-01",
            "end_date": "2025-06-01",  # end before start
            "adults": 2,
            "budget": 5000.0,
            "trip_type": "sightseeing",
        },
    )
    assert response.status_code == 422


def test_itinerary_zero_adults_returns_422() -> None:
    from wander_agent.main import app

    client = TestClient(app)
    response = client.post(
        "/itinerary",
        json={
            "destination": "Italy",
            "start_date": "2025-07-01",
            "end_date": "2025-07-11",
            "adults": 0,
            "budget": 5000.0,
            "trip_type": "sightseeing",
        },
    )
    assert response.status_code == 422


def test_itinerary_streams_sse_events() -> None:
    from wander_agent.main import app

    with patch("wander_agent.main.graph") as mock_graph:
        mock_graph.astream_events = _mock_stream

        client = TestClient(app)
        with client.stream(
            "POST",
            "/itinerary",
            json={
                "destination": "Italy",
                "start_date": "2025-07-01",
                "end_date": "2025-07-11",
                "adults": 2,
                "children": 0,
                "budget": 5000.0,
                "trip_type": "sightseeing",
            },
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

    event_types = [e["event"] for e in events]
    assert "status" in event_types
    assert "complete" in event_types

    complete_event = next(e for e in events if e["event"] == "complete")
    assert "itinerary" in complete_event
    assert complete_event["itinerary"]["destination"] == "Italy"


def test_itinerary_status_events_include_node_name() -> None:
    from wander_agent.main import app

    with patch("wander_agent.main.graph") as mock_graph:
        mock_graph.astream_events = _mock_stream

        client = TestClient(app)
        with client.stream(
            "POST",
            "/itinerary",
            json={
                "destination": "Italy",
                "start_date": "2025-07-01",
                "end_date": "2025-07-11",
                "adults": 2,
                "children": 0,
                "budget": 5000.0,
                "trip_type": "sightseeing",
            },
        ) as response:
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

    status_events = [e for e in events if e["event"] == "status"]
    assert len(status_events) > 0
    for e in status_events:
        assert "node" in e
        assert "message" in e
