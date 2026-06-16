# Travel Service Design

**Date:** 2026-06-15
**Status:** Approved

## Problem

The travel-agent monorepo needs a mock flight-search microservice to complement the
existing listings service. The service must generate realistic one-way flight options
for a given route using an LLM, returning a fixed set of 3 results each time.

## API

`GET /flights`

| Param | Type | Required | Constraint |
|---|---|---|---|
| `departure_airport` | string | yes | 3-char IATA code |
| `arrival_airport` | string | yes | 3-char IATA code |
| `traveler_count` | integer | yes | ≥ 1 |
| `departure_datetime` | ISO 8601 datetime | no | Mutually exclusive with `arrival_datetime` |
| `arrival_datetime` | ISO 8601 datetime | no | Mutually exclusive with `departure_datetime` |

Exactly one of `departure_datetime` / `arrival_datetime` must be provided.
- Neither provided → 422
- Both provided → 400

## Data Models

```
Layover { airport: str, duration_minutes: int > 0 }
FlightOption { airline, departure_datetime, arrival_datetime, cost_per_ticket: float > 0, layovers: list[Layover] }
FlightsPayload { options: list[FlightOption] (exactly 3) }   ← LLM output
FlightsResponse { departure_airport, arrival_airport, traveler_count, options }  ← API response
```

## Architecture

Mirrors `services/listings`:
- Module-level `chain = build_flights_chain()` (no lifespan hook needed)
- Chain: `ChatPromptTemplate | ChatGoogleGenerativeAI.with_structured_output(FlightsPayload)`
- No external enrichment tools
- `_format_request()` helper converts query params to natural-language string

## Error Handling

| Condition | Status |
|---|---|
| Both datetimes provided | 400 |
| Neither datetime provided | 422 |
| Missing required params | 422 (FastAPI default) |
| Chain raises | 502 |

## Testing

TestClient + `unittest.mock.patch("travel.main.chain")` per test. Covers happy paths
(departure_datetime, arrival_datetime), all error codes, and chain failure.
