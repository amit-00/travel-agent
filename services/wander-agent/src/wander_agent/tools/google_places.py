import os
from typing import TypedDict

from google.api_core.client_options import ClientOptions
from google.maps import places_v1
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

_FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.rating,places.priceLevel,places.types"


class _PlaceResult(TypedDict):
    name: str
    address: str
    rating: float | None
    price_level: int | None
    place_id: str
    types: list[str]


class _GooglePlacesBaseTool(BaseTool):
    _client: places_v1.PlacesClient = PrivateAttr()

    def model_post_init(self, __context: object) -> None:
        api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY environment variable is not set")
        self._client = places_v1.PlacesClient(
            client_options=ClientOptions(api_key=api_key)
        )

    def _fetch(
        self, query: str, location: str, place_type: str
    ) -> list[_PlaceResult]:
        request = places_v1.SearchTextRequest(
            text_query=f"{query} in {location}",
            included_type=place_type,
            max_result_count=20,
        )
        response = self._client.search_text(
            request,
            metadata=[("x-goog-fieldmask", _FIELD_MASK)],
        )
        return [
            _PlaceResult(
                name=place.display_name.text,
                address=place.formatted_address,
                rating=place.rating or None,
                price_level=int(place.price_level) or None,
                place_id=place.id,
                types=list(place.types),
            )
            for place in response.places
        ]


class _StaysArgs(BaseModel):
    query: str = Field(
        description="Search query, e.g. 'charming coastal towns near Amalfi'"
    )
    location: str = Field(
        description="Region or area to search within, e.g. 'Campania, Italy'"
    )


class _ActivitiesArgs(BaseModel):
    query: str = Field(
        description="Activity search query, e.g. 'museums and ancient ruins'"
    )
    location: str = Field(
        description="City or district to search within, e.g. 'Rome, Italy'"
    )


class _RestaurantsArgs(BaseModel):
    query: str = Field(
        description="Dining search query, e.g. 'local seafood restaurants'"
    )
    location: str = Field(
        description="City or neighbourhood to search within, e.g. 'Naples, Italy'"
    )


class GooglePlacesStaysTool(_GooglePlacesBaseTool):
    name: str = "google_places_stays"
    description: str = (
        "Find sub-destinations and stay locations for a vacation. "
        "Use to discover cities, towns, or neighbourhoods for an itinerary."
    )
    args_schema: type[BaseModel] = _StaysArgs

    def _run(self, query: str, location: str) -> list[_PlaceResult]:
        return self._fetch(query, location, place_type="locality")


class GooglePlacesActivitiesTool(_GooglePlacesBaseTool):
    name: str = "google_places_activities"
    description: str = (
        "Find activities, attractions, and points of interest at a destination. "
        "Use to discover landmarks, museums, parks, and experiences for an itinerary."
    )
    args_schema: type[BaseModel] = _ActivitiesArgs

    def _run(self, query: str, location: str) -> list[_PlaceResult]:
        return self._fetch(query, location, place_type="tourist_attraction")


class GooglePlacesRestaurantsTool(_GooglePlacesBaseTool):
    name: str = "google_places_restaurants"
    description: str = (
        "Find restaurants and dining options at a vacation destination. "
        "Use to discover local cuisine, cafes, and dining experiences for an itinerary."
    )
    args_schema: type[BaseModel] = _RestaurantsArgs

    def _run(self, query: str, location: str) -> list[_PlaceResult]:
        return self._fetch(query, location, place_type="restaurant")
