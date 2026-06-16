from datetime import datetime
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .chain import build_flights_chain
from .models import FlightsPayload, FlightsResponse

load_dotenv()

app = FastAPI(title="Travel API", version="0.1.0")
chain = build_flights_chain()


class HealthResponse(BaseModel):
    status: str


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/flights")
async def get_flights(
    departure_airport: Annotated[str, Query(min_length=3, max_length=3)],
    arrival_airport: Annotated[str, Query(min_length=3, max_length=3)],
    traveler_count: Annotated[int, Query(ge=1)],
    departure_datetime: Annotated[datetime | None, Query()] = None,
    arrival_datetime: Annotated[datetime | None, Query()] = None,
) -> FlightsResponse:
    if departure_datetime is None and arrival_datetime is None:
        raise HTTPException(
            status_code=422,
            detail="At least one of departure_datetime or arrival_datetime is required.",
        )
    if departure_datetime is not None and arrival_datetime is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either departure_datetime or arrival_datetime, not both.",
        )

    request_text = _format_request(
        departure_airport=departure_airport,
        arrival_airport=arrival_airport,
        traveler_count=traveler_count,
        departure_datetime=departure_datetime,
        arrival_datetime=arrival_datetime,
    )

    try:
        payload: FlightsPayload = await chain.ainvoke({"request": request_text})
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Flight search failed") from exc

    return FlightsResponse(
        departure_airport=departure_airport,
        arrival_airport=arrival_airport,
        traveler_count=traveler_count,
        options=payload.options,
    )


def _format_request(
    *,
    departure_airport: str,
    arrival_airport: str,
    traveler_count: int,
    departure_datetime: datetime | None,
    arrival_datetime: datetime | None,
) -> str:
    parts = [
        f"Route: {departure_airport} → {arrival_airport}",
        f"Travellers: {traveler_count}",
    ]
    if departure_datetime is not None:
        parts.append(f"Departure: {departure_datetime.isoformat()}")
    else:
        assert arrival_datetime is not None
        parts.append(f"Must arrive by: {arrival_datetime.isoformat()}")
    return "\n".join(parts)
