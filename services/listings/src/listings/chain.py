import asyncio

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI

from .models import ListingItem, ListingsPayload
from .tools import search_pexels_image

_SYSTEM_PROMPT = """\
You are a property listings fabricator for a travel app demo. Your job is to \
generate exactly 3 realistic but entirely fictional Airbnb-style property listings \
that match the search criteria provided.

For each listing produce:
- A compelling title that reflects the location and property character
- A realistic price per night appropriate to the location and property type
- Appropriate bedrooms count and max guest capacity
- A list of 4-6 relevant amenities
- A 2-3 sentence description highlighting key features
- A realistic rating between 4.0 and 5.0
- A plausible neighborhood name within or near the requested location

Make the 3 listings diverse in price, style, and neighborhood. \
Honour all constraints given (price range, amenities, property type, guest count).\
"""


async def _enrich_with_images(payload: ListingsPayload) -> ListingsPayload:
    async def fetch(listing: ListingItem) -> ListingItem:
        query = f"{listing.property_type} {listing.neighborhood} vacation rental"
        url = await search_pexels_image.ainvoke({"query": query})
        return listing.model_copy(update={"image_url": url})

    enriched = await asyncio.gather(*[fetch(item) for item in payload.listings])
    return ListingsPayload(listings=list(enriched))


def build_listings_chain() -> Runnable[dict[str, str], ListingsPayload]:
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
    structured_model = model.with_structured_output(ListingsPayload)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", "{request}"),
        ]
    )

    return prompt | structured_model | RunnableLambda(_enrich_with_images)
