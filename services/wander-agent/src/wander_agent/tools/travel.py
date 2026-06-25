import os

import httpx


async def search_flights(
    departure_airport: str,
    arrival_airport: str,
    traveler_count: int,
    departure_datetime: str,
) -> list[dict[str, object]]:
    base_url = os.environ.get("TRAVEL_SERVICE_URL")
    if not base_url:
        raise ValueError("TRAVEL_SERVICE_URL environment variable is not set")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/flights",
            params={
                "departure_airport": departure_airport,
                "arrival_airport": arrival_airport,
                "traveler_count": traveler_count,
                "departure_datetime": departure_datetime,
            },
        )
    response.raise_for_status()
    return list(response.json().get("options", []))
