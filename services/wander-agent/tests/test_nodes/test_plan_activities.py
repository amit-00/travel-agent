from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from wander_agent.state import PlanActivitiesInput, Stay, StayWithListings, TripRequest


def _make_input() -> PlanActivitiesInput:
    stay = Stay(
        location="Rome",
        airport_code="FCO",
        check_in=date(2025, 7, 1),
        check_out=date(2025, 7, 4),
        rationale="",
    )
    return PlanActivitiesInput(
        stay_with_listings=StayWithListings(
            stay=stay,
            accommodation_options=[
                {
                    "title": "Apt A",
                    "neighborhood": "Trastevere",
                    "check_in": "2025-07-01",
                }
            ],
        ),
        request=TripRequest(
            destination="Italy",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 11),
            adults=2,
            children=0,
            budget=5000.0,
            trip_type="sightseeing",
        ),
    )


def _make_mock_days() -> list[dict[str, object]]:
    return [
        {
            "date": date(2025, 7, 1),
            "schedule": [
                {
                    "time": "09:00",
                    "name": "Colosseum",
                    "type": "sightseeing",
                    "duration_hours": 2.0,
                    "cost_estimate": 20.0,
                    "notes": "",
                }
            ],
        },
        {
            "date": date(2025, 7, 2),
            "schedule": [
                {
                    "time": "10:00",
                    "name": "Vatican Museums",
                    "type": "sightseeing",
                    "duration_hours": 3.0,
                    "cost_estimate": 25.0,
                    "notes": "Book in advance",
                }
            ],
        },
    ]


@pytest.mark.asyncio
async def test_plan_activities_returns_stay_with_activities() -> None:
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=_make_mock_days())

    with patch(
        "wander_agent.nodes.plan_activities.build_plan_activities_chain",
        return_value=mock_chain,
    ):
        from wander_agent.nodes.plan_activities import plan_activities

        result = await plan_activities(_make_input())

    assert "activity_results" in result
    assert len(result["activity_results"]) == 1
    entry = result["activity_results"][0]
    assert entry["stay"]["location"] == "Rome"
    assert len(entry["days"]) == 3  # Jul 1, 2, 3 (check_out Jul 4 is exclusive)
    assert entry["days"][0]["schedule"][0]["name"] == "Colosseum"


@pytest.mark.asyncio
async def test_plan_activities_covers_all_stay_dates() -> None:
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=_make_mock_days())

    with patch(
        "wander_agent.nodes.plan_activities.build_plan_activities_chain",
        return_value=mock_chain,
    ):
        from wander_agent.nodes.plan_activities import plan_activities

        result = await plan_activities(_make_input())

    days = result["activity_results"][0]["days"]
    day_dates = [d["date"] for d in days]
    assert date(2025, 7, 1) in day_dates
    assert date(2025, 7, 2) in day_dates
