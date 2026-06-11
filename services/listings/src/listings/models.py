from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class PropertyType(StrEnum):
    apartment = "apartment"
    house = "house"
    cabin = "cabin"
    villa = "villa"
    condo = "condo"


class ListingItem(BaseModel):
    id: str
    title: str
    property_type: str
    neighborhood: str
    bedrooms: int
    max_guests: int
    price_per_night: float
    amenities: list[str]
    description: str
    rating: float = Field(ge=4.0, le=5.0)
    image_url: str = ""


class ListingsPayload(BaseModel):
    listings: list[ListingItem]


class ListingsResponse(BaseModel):
    listings: list[ListingItem]
    location: str
    check_in: date
    check_out: date
