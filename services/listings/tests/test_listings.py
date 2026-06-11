from unittest.mock import patch

from fastapi.testclient import TestClient
from listings.main import app
from listings.models import ListingItem, ListingsPayload

client = TestClient(app)

VALID_PARAMS = {
    "location": "Sedona, AZ",
    "check_in": "2026-07-01",
    "check_out": "2026-07-05",
    "adults": 2,
}

FAKE_LISTINGS = [
    ListingItem(
        id="00000000-0000-0000-0000-000000000001",
        title="Desert Casita with Mountain Views",
        property_type="cabin",
        neighborhood="Uptown Sedona",
        bedrooms=2,
        max_guests=4,
        price_per_night=189.0,
        amenities=["WiFi", "Pool", "Kitchen"],
        description="A beautiful casita with stunning red rock views.",
        rating=4.8,
        image_url="https://images.listings-api.dev/photos/00000000-0000-0000-0000-000000000001.jpg",
    ),
    ListingItem(
        id="00000000-0000-0000-0000-000000000002",
        title="Modern Loft in West Sedona",
        property_type="apartment",
        neighborhood="West Sedona",
        bedrooms=1,
        max_guests=2,
        price_per_night=145.0,
        amenities=["WiFi", "Gym", "Parking"],
        description="Sleek modern loft steps from galleries and restaurants.",
        rating=4.6,
        image_url="https://images.listings-api.dev/photos/00000000-0000-0000-0000-000000000002.jpg",
    ),
    ListingItem(
        id="00000000-0000-0000-0000-000000000003",
        title="Creekside Cottage",
        property_type="house",
        neighborhood="Oak Creek Canyon",
        bedrooms=3,
        max_guests=6,
        price_per_night=265.0,
        amenities=["WiFi", "Hot Tub", "Fireplace", "Pet-friendly"],
        description="Cozy cottage nestled beside Oak Creek with private hot tub.",
        rating=4.9,
        image_url="https://images.listings-api.dev/photos/00000000-0000-0000-0000-000000000003.jpg",
    ),
]


def make_payload(listings: list[ListingItem] = FAKE_LISTINGS) -> ListingsPayload:
    return ListingsPayload(listings=listings)


def test_get_listings_returns_three_results() -> None:
    with patch("listings.main.chain") as mock_chain:
        mock_chain.invoke.return_value = make_payload()
        response = client.get("/listings", params=VALID_PARAMS)

    assert response.status_code == 200
    body = response.json()
    assert len(body["listings"]) == 3


def test_get_listings_response_echoes_location_and_dates() -> None:
    with patch("listings.main.chain") as mock_chain:
        mock_chain.invoke.return_value = make_payload()
        response = client.get("/listings", params=VALID_PARAMS)

    body = response.json()
    assert body["location"] == "Sedona, AZ"
    assert body["check_in"] == "2026-07-01"
    assert body["check_out"] == "2026-07-05"


def test_get_listings_passes_all_params_to_chain() -> None:
    params = {
        **VALID_PARAMS,
        "children": 1,
        "min_price": 100,
        "max_price": 300,
        "amenities": ["pool", "wifi"],
        "property_type": "cabin",
    }
    with patch("listings.main.chain") as mock_chain:
        mock_chain.invoke.return_value = make_payload()
        response = client.get("/listings", params=params)

    assert response.status_code == 200
    call_args = mock_chain.invoke.call_args[0][0]
    assert "pool" in call_args["request"]
    assert "cabin" in call_args["request"]


def test_get_listings_rejects_check_out_before_check_in() -> None:
    params = {**VALID_PARAMS, "check_in": "2026-07-05", "check_out": "2026-07-01"}
    response = client.get("/listings", params=params)
    assert response.status_code == 422


def test_get_listings_rejects_zero_adults() -> None:
    params = {**VALID_PARAMS, "adults": 0}
    response = client.get("/listings", params=params)
    assert response.status_code == 422


def test_get_listings_rejects_missing_location() -> None:
    params = {k: v for k, v in VALID_PARAMS.items() if k != "location"}
    response = client.get("/listings", params=params)
    assert response.status_code == 422


def test_get_listings_returns_502_on_chain_failure() -> None:
    with patch("listings.main.chain") as mock_chain:
        mock_chain.invoke.side_effect = RuntimeError("LLM unavailable")
        response = client.get("/listings", params=VALID_PARAMS)

    assert response.status_code == 502
