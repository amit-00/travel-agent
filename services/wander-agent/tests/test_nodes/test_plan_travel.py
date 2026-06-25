from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from wander_agent.state import PlanTravelInput, Stay


def _make_input() -> PlanTravelInput:
    return PlanTravelInput(
        from_stay=Stay(
            location="Rome",
            airport_code="FCO",
            check_in=date(2025, 7, 1),
            check_out=date(2025, 7, 4),
            rationale="",
        ),
        to_stay=Stay(
            location="Florence",
            airport_code="FLR",
            check_in=date(2025, 7, 4),
            check_out=date(2025, 7, 8),
            rationale="",
        ),
        traveler_count=2,
    )


@pytest.mark.asyncio
async def test_plan_travel_returns_travel_leg() -> None:
    mock_options = [
        {"airline": "Alitalia", "cost_per_ticket": 120.0},
        {"airline": "Ryanair", "cost_per_ticket": 80.0},
        {"airline": "EasyJet", "cost_per_ticket": 95.0},
    ]

    with patch(
        "wander_agent.nodes.plan_travel.search_flights",
        new=AsyncMock(return_value=mock_options),
    ):
        from wander_agent.nodes.plan_travel import plan_travel

        result = await plan_travel(_make_input())

    assert "travel_results" in result
    assert len(result["travel_results"]) == 1
    leg = result["travel_results"][0]
    assert leg["from_location"] == "Rome"
    assert leg["from_airport"] == "FCO"
    assert leg["to_location"] == "Florence"
    assert leg["to_airport"] == "FLR"
    assert len(leg["options"]) == 3


@pytest.mark.asyncio
async def test_plan_travel_empty_options_on_error() -> None:
    with patch(
        "wander_agent.nodes.plan_travel.search_flights",
        new=AsyncMock(side_effect=Exception("service down")),
    ):
        from wander_agent.nodes.plan_travel import plan_travel

        result = await plan_travel(_make_input())

    assert result["travel_results"][0]["options"] == []
