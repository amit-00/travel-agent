from datetime import date
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .chain import build_listings_chain
from .models import ListingsResponse, PropertyType

load_dotenv()

app = FastAPI(title="Listings API", version="0.1.0")
chain = build_listings_chain()


class HealthResponse(BaseModel):
    status: str


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/listings")
async def get_listings(
    location: Annotated[str, Query(min_length=1, max_length=200)],
    check_in: date,
    check_out: date,
    adults: Annotated[int, Query(ge=1)],
    children: Annotated[int, Query(ge=0)] = 0,
    min_price: float | None = None,
    max_price: float | None = None,
    amenities: Annotated[list[str], Query(max_length=50)] = [],
    property_type: PropertyType | None = None,
) -> ListingsResponse:
    if len(amenities) > 20:
        raise HTTPException(
            status_code=422, detail="amenities must not exceed 20 items"
        )
    if check_in >= check_out:
        raise HTTPException(
            status_code=422,
            detail="check_out must be strictly after check_in",
        )

    request_text = _format_request(
        location=location,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        children=children,
        min_price=min_price,
        max_price=max_price,
        amenities=amenities,
        property_type=property_type,
    )

    try:
        payload = await chain.ainvoke({"request": request_text})
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail="Listing generation failed"
        ) from exc

    return ListingsResponse(
        listings=payload.listings,
        location=location,
        check_in=check_in,
        check_out=check_out,
    )


def _format_request(
    *,
    location: str,
    check_in: date,
    check_out: date,
    adults: int,
    children: int,
    min_price: float | None,
    max_price: float | None,
    amenities: list[str],
    property_type: PropertyType | None,
) -> str:
    nights = (check_out - check_in).days
    parts = [
        f"Location: {location}",
        f"Check-in: {check_in}  Check-out: {check_out} ({nights} nights)",
        f"Guests: {adults} adult(s), {children} child(ren)",
    ]
    if property_type:
        parts.append(f"Property type: {property_type.value}")
    if min_price is not None or max_price is not None:
        lo = f"${min_price:.0f}" if min_price is not None else "any"
        hi = f"${max_price:.0f}" if max_price is not None else "any"
        parts.append(f"Price range: {lo}–{hi} per night")
    if amenities:
        parts.append(f"Required amenities: {', '.join(amenities)}")
    return "\n".join(parts)
