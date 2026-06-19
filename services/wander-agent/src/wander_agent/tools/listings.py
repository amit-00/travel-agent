import os
from datetime import date

import httpx


async def search_listings(
    location: str,
    check_in: date,
    check_out: date,
    adults: int,
    children: int = 0,
) -> list[dict[str, object]]:
    base_url = os.environ.get("LISTINGS_SERVICE_URL")
    if not base_url:
        raise ValueError("LISTINGS_SERVICE_URL environment variable is not set")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/listings",
            params={
                "location": location,
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat(),
                "adults": adults,
                "children": children,
            },
        )
    response.raise_for_status()
    return list(response.json().get("listings", []))
