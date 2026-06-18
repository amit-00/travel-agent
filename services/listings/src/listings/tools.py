import os

import httpx
from langchain_core.tools import tool

_FALLBACK_IMAGE = "https://images.listings-api.dev/photos/placeholder.jpg"


@tool
async def search_pexels_image(query: str) -> str:
    """Search Pexels for a landscape photo matching the query. Returns the image URL."""
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        raise ValueError("PEXELS_API_KEY environment variable is not set")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": 1, "orientation": "landscape"},
        )
    response.raise_for_status()

    photos = response.json().get("photos", [])
    if not photos:
        return _FALLBACK_IMAGE

    return str(photos[0]["src"]["large"])
