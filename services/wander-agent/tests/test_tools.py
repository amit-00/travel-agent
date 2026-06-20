import os
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGooglePlacesTools:
    def test_stays_raises_without_api_key(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "GOOGLE_PLACES_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from wander_agent.tools.google_places import GooglePlacesStaysTool

            with pytest.raises(ValueError, match="GOOGLE_PLACES_API_KEY"):
                GooglePlacesStaysTool()

    def test_activities_raises_without_api_key(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "GOOGLE_PLACES_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from wander_agent.tools.google_places import GooglePlacesActivitiesTool

            with pytest.raises(ValueError, match="GOOGLE_PLACES_API_KEY"):
                GooglePlacesActivitiesTool()

    def test_restaurants_raises_without_api_key(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "GOOGLE_PLACES_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from wander_agent.tools.google_places import GooglePlacesRestaurantsTool

            with pytest.raises(ValueError, match="GOOGLE_PLACES_API_KEY"):
                GooglePlacesRestaurantsTool()

    def test_stays_run_searches_with_locality_type(self) -> None:
        mock_client = MagicMock()
        mock_client.search_text.return_value.places = []

        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test-key"}):
            with patch("google.maps.places_v1.PlacesClient", return_value=mock_client):
                from wander_agent.tools.google_places import GooglePlacesStaysTool

                tool = GooglePlacesStaysTool()

        tool._run(query="coastal towns", location="Amalfi Coast, Italy")

        mock_client.search_text.assert_called_once()
        assert mock_client.search_text.call_args.args[0].included_type == "locality"

    def test_activities_run_searches_with_tourist_attraction_type(self) -> None:
        mock_client = MagicMock()
        mock_client.search_text.return_value.places = []

        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test-key"}):
            with patch("google.maps.places_v1.PlacesClient", return_value=mock_client):
                from wander_agent.tools.google_places import GooglePlacesActivitiesTool

                tool = GooglePlacesActivitiesTool()

        tool._run(query="museums and parks", location="Rome, Italy")

        mock_client.search_text.assert_called_once()
        assert (
            mock_client.search_text.call_args.args[0].included_type
            == "tourist_attraction"
        )

    def test_restaurants_run_searches_with_restaurant_type(self) -> None:
        mock_client = MagicMock()
        mock_client.search_text.return_value.places = []

        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test-key"}):
            with patch("google.maps.places_v1.PlacesClient", return_value=mock_client):
                from wander_agent.tools.google_places import GooglePlacesRestaurantsTool

                tool = GooglePlacesRestaurantsTool()

        tool._run(query="local seafood", location="Naples, Italy")

        mock_client.search_text.assert_called_once()
        assert mock_client.search_text.call_args.args[0].included_type == "restaurant"

    def test_run_returns_normalized_place_results(self) -> None:
        mock_place = MagicMock()
        mock_place.display_name.text = "Colosseum"
        mock_place.formatted_address = "Piazza del Colosseo, 1, 00184 Roma RM, Italy"
        mock_place.rating = 4.8
        mock_place.price_level = 2
        mock_place.id = "ChIJrRMgU7ZhLxMRIAKX_aUZCAQ"
        mock_place.types = ["tourist_attraction", "point_of_interest"]

        mock_client = MagicMock()
        mock_client.search_text.return_value.places = [mock_place]

        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test-key"}):
            with patch("google.maps.places_v1.PlacesClient", return_value=mock_client):
                from wander_agent.tools.google_places import GooglePlacesActivitiesTool

                tool = GooglePlacesActivitiesTool()

        results = tool._run(query="ancient ruins", location="Rome, Italy")

        assert len(results) == 1
        result = results[0]
        assert result["name"] == "Colosseum"
        assert result["address"] == "Piazza del Colosseo, 1, 00184 Roma RM, Italy"
        assert result["rating"] == 4.8
        assert result["price_level"] == 2
        assert result["place_id"] == "ChIJrRMgU7ZhLxMRIAKX_aUZCAQ"
        assert "tourist_attraction" in result["types"]

    def test_run_handles_missing_optional_fields(self) -> None:
        mock_place = MagicMock()
        mock_place.display_name.text = "Small Trattoria"
        mock_place.formatted_address = "Via Roma 1, Naples, Italy"
        mock_place.rating = 0.0
        mock_place.price_level = 0
        mock_place.id = "abc123"
        mock_place.types = ["restaurant"]

        mock_client = MagicMock()
        mock_client.search_text.return_value.places = [mock_place]

        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test-key"}):
            with patch("google.maps.places_v1.PlacesClient", return_value=mock_client):
                from wander_agent.tools.google_places import GooglePlacesRestaurantsTool

                tool = GooglePlacesRestaurantsTool()

        results = tool._run(query="trattorias", location="Naples, Italy")

        assert results[0]["rating"] is None
        assert results[0]["price_level"] is None


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
