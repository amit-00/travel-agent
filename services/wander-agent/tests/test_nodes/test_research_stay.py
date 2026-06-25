from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from wander_agent.state import ResearchStayInput, Stay, TripRequest


def _make_input() -> ResearchStayInput:
    return ResearchStayInput(
        stay=Stay(
            location="Rome",
            airport_code="FCO",
            check_in=date(2025, 7, 1),
            check_out=date(2025, 7, 4),
            rationale="Great city",
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


@pytest.mark.asyncio
async def test_research_stay_returns_stay_with_listings() -> None:
    mock_listings = [
        {"id": "1", "title": "Apt A", "price_per_night": 100.0},
        {"id": "2", "title": "Apt B", "price_per_night": 150.0},
        {"id": "3", "title": "Apt C", "price_per_night": 200.0},
    ]

    with patch(
        "wander_agent.nodes.research_stay.search_listings",
        new_callable=lambda: lambda **kwargs: AsyncMock(return_value=mock_listings)(),
    ):
        with patch(
            "wander_agent.nodes.research_stay.search_listings",
            new=AsyncMock(return_value=mock_listings),
        ):
            from wander_agent.nodes.research_stay import research_stay

            result = await research_stay(_make_input())

    assert "accommodation_results" in result
    assert len(result["accommodation_results"]) == 1
    entry = result["accommodation_results"][0]
    assert entry["stay"]["location"] == "Rome"
    assert len(entry["accommodation_options"]) == 3


@pytest.mark.asyncio
async def test_research_stay_empty_listings_on_error() -> None:
    with patch(
        "wander_agent.nodes.research_stay.search_listings",
        new=AsyncMock(side_effect=Exception("service down")),
    ):
        from wander_agent.nodes.research_stay import research_stay

        result = await research_stay(_make_input())

    assert result["accommodation_results"][0]["accommodation_options"] == []
