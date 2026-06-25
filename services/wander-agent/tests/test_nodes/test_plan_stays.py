from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wander_agent.state import Stay, TripRequest, WanderState


def _make_state() -> WanderState:
    return WanderState(
        request=TripRequest(
            destination="Italy",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 11),
            adults=2,
            children=0,
            budget=5000.0,
            trip_type="sightseeing",
        ),
        stays=[],
        accommodation_results=[],
        travel_results=[],
        activity_results=[],
        itinerary=None,
    )


def _make_stay(location: str, check_in: str, check_out: str) -> Stay:
    return Stay(
        location=location,
        airport_code="FCO",
        check_in=date.fromisoformat(check_in),
        check_out=date.fromisoformat(check_out),
        rationale="Great city",
    )


@pytest.mark.asyncio
async def test_plan_stays_returns_list_of_stays() -> None:
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(
        return_value=[
            _make_stay("Rome", "2025-07-01", "2025-07-04"),
            _make_stay("Florence", "2025-07-04", "2025-07-08"),
        ]
    )

    with patch(
        "wander_agent.nodes.plan_stays.build_plan_stays_chain", return_value=mock_chain
    ):
        from wander_agent.nodes.plan_stays import plan_stays

        state = _make_state()
        result = await plan_stays(state)

    assert "stays" in result
    stays = result["stays"]
    assert len(stays) == 2
    assert stays[0]["location"] == "Rome"
    assert stays[1]["location"] == "Florence"
    assert stays[0]["check_in"] == date(2025, 7, 1)
    assert stays[0]["check_out"] == date(2025, 7, 4)


@pytest.mark.asyncio
async def test_plan_stays_single_destination() -> None:
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(
        return_value=[_make_stay("Paris", "2025-07-01", "2025-07-11")]
    )

    with patch(
        "wander_agent.nodes.plan_stays.build_plan_stays_chain", return_value=mock_chain
    ):
        from wander_agent.nodes.plan_stays import plan_stays

        state = _make_state()
        result = await plan_stays(state)

    assert len(result["stays"]) == 1
    assert result["stays"][0]["location"] == "Paris"
