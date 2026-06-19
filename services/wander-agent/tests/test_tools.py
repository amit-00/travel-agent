import os
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSearchTool:
    def test_tavily_tool_is_callable(self) -> None:
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}):
            from langchain_tavily import TavilySearch
            from wander_agent.tools.search import build_search_tool

            tool = build_search_tool()
            assert isinstance(tool, TavilySearch)

    def test_tavily_tool_raises_without_api_key(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "TAVILY_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from wander_agent.tools.search import build_search_tool

            with pytest.raises(ValueError, match="TAVILY_API_KEY"):
                build_search_tool()


class TestListingsTool:
    @pytest.mark.asyncio
    async def test_search_listings_returns_options(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "listings": [
                {"id": "1", "title": "Apt A", "price_per_night": 100.0},
                {"id": "2", "title": "Apt B", "price_per_night": 150.0},
                {"id": "3", "title": "Apt C", "price_per_night": 200.0},
            ],
            "location": "Rome",
            "check_in": "2025-07-01",
            "check_out": "2025-07-04",
        }

        with patch.dict(os.environ, {"LISTINGS_SERVICE_URL": "http://listings:8000"}):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response
                from wander_agent.tools.listings import search_listings

                result = await search_listings(
                    location="Rome",
                    check_in=date(2025, 7, 1),
                    check_out=date(2025, 7, 4),
                    adults=2,
                    children=0,
                )
                assert len(result) == 3
                assert result[0]["title"] == "Apt A"

    @pytest.mark.asyncio
    async def test_search_listings_raises_without_url(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "LISTINGS_SERVICE_URL"}
        with patch.dict(os.environ, env, clear=True):
            from wander_agent.tools.listings import search_listings

            with pytest.raises(ValueError, match="LISTINGS_SERVICE_URL"):
                await search_listings(
                    location="Rome",
                    check_in=date(2025, 7, 1),
                    check_out=date(2025, 7, 4),
                    adults=2,
                    children=0,
                )


class TestTravelTool:
    @pytest.mark.asyncio
    async def test_search_flights_returns_options(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "options": [
                {"airline": "Alitalia", "cost_per_ticket": 120.0},
                {"airline": "Ryanair", "cost_per_ticket": 80.0},
                {"airline": "EasyJet", "cost_per_ticket": 95.0},
            ],
            "departure_airport": "FCO",
            "arrival_airport": "FLR",
            "traveler_count": 2,
        }

        with patch.dict(os.environ, {"TRAVEL_SERVICE_URL": "http://travel:8000"}):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response
                from wander_agent.tools.travel import search_flights

                result = await search_flights(
                    departure_airport="FCO",
                    arrival_airport="FLR",
                    traveler_count=2,
                    departure_datetime="2025-07-04T10:00:00",
                )
                assert len(result) == 3
                assert result[0]["airline"] == "Alitalia"

    @pytest.mark.asyncio
    async def test_search_flights_raises_without_url(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "TRAVEL_SERVICE_URL"}
        with patch.dict(os.environ, env, clear=True):
            from wander_agent.tools.travel import search_flights

            with pytest.raises(ValueError, match="TRAVEL_SERVICE_URL"):
                await search_flights(
                    departure_airport="FCO",
                    arrival_airport="FLR",
                    traveler_count=2,
                    departure_datetime="2025-07-04T10:00:00",
                )
