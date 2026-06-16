from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from travel.main import app
from travel.models import FlightOption, FlightsPayload, Layover

client = TestClient(app)

VALID_PARAMS = {
    "departure_airport": "JFK",
    "arrival_airport": "LAX",
    "traveler_count": 2,
    "departure_datetime": "2026-07-01T10:00:00",
}

_OPTION = FlightOption(
    airline="Delta",
    departure_datetime=datetime(2026, 7, 1, 10, 0),
    arrival_datetime=datetime(2026, 7, 1, 16, 30),
    cost_per_ticket=299.99,
    layovers=[Layover(airport="ORD", duration_minutes=90)],
)

FAKE_PAYLOAD = FlightsPayload(options=[_OPTION, _OPTION, _OPTION])


def test_get_flights_with_departure_datetime_returns_three_options() -> None:
    with patch("travel.main.chain") as mock_chain:
        mock_chain.ainvoke = AsyncMock(return_value=FAKE_PAYLOAD)
        response = client.get("/flights", params=VALID_PARAMS)

    assert response.status_code == 200
    assert len(response.json()["options"]) == 3


def test_get_flights_response_echoes_request_context() -> None:
    with patch("travel.main.chain") as mock_chain:
        mock_chain.ainvoke = AsyncMock(return_value=FAKE_PAYLOAD)
        response = client.get("/flights", params=VALID_PARAMS)

    body = response.json()
    assert body["departure_airport"] == "JFK"
    assert body["arrival_airport"] == "LAX"
    assert body["traveler_count"] == 2


def test_get_flights_with_arrival_datetime_returns_three_options() -> None:
    params = {
        "departure_airport": "SFO",
        "arrival_airport": "ORD",
        "traveler_count": 1,
        "arrival_datetime": "2026-07-01T18:00:00",
    }
    with patch("travel.main.chain") as mock_chain:
        mock_chain.ainvoke = AsyncMock(return_value=FAKE_PAYLOAD)
        response = client.get("/flights", params=params)

    assert response.status_code == 200
    assert len(response.json()["options"]) == 3


def test_get_flights_both_datetimes_returns_400() -> None:
    params = {**VALID_PARAMS, "arrival_datetime": "2026-07-01T18:00:00"}
    response = client.get("/flights", params=params)
    assert response.status_code == 400


def test_get_flights_no_datetime_returns_422() -> None:
    params = {
        "departure_airport": "JFK",
        "arrival_airport": "LAX",
        "traveler_count": 2,
    }
    response = client.get("/flights", params=params)
    assert response.status_code == 422


def test_get_flights_zero_travellers_returns_422() -> None:
    params = {**VALID_PARAMS, "traveler_count": 0}
    response = client.get("/flights", params=params)
    assert response.status_code == 422


def test_get_flights_returns_502_on_chain_failure() -> None:
    with patch("travel.main.chain") as mock_chain:
        mock_chain.ainvoke = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        response = client.get("/flights", params=VALID_PARAMS)

    assert response.status_code == 502
