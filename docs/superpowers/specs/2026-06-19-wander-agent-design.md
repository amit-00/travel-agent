# wander-agent Design Spec

**Date:** 2026-06-19
**Status:** Implemented

## Context

The existing `services/agent` skeleton is replaced with `wander-agent`: a full LangGraph + FastAPI service that accepts trip parameters and produces a structured itinerary JSON via a streaming SSE endpoint.

The agent coordinates with the `listings` service (8001) and `travel` service (8002) as downstream tool targets. Tavily web search drives destination and activity research. All LLM calls use Google Gemini via `langchain-google-genai`, keeping `GOOGLE_API_KEY` as the only LLM credential.

---

## Architecture

### Graph Topology (LangGraph Send API fan-out)

```
POST /itinerary
      │
 [plan_stays]  ← Gemini 2.5 Pro + Tavily
      │  Send × N stays
      ▼
 [research_stay]  ← Gemini 2.5 Flash-Lite + listings HTTP tool  (parallel per stay)
      │  reduce → fanout_travel (barrier)
      ▼
 [plan_travel]  ← Gemini 2.5 Flash-Lite + travel HTTP tool  (parallel per inter-stay leg)
      │  reduce → fanout_activities (barrier)
      ▼
 [plan_activities]  ← Gemini 2.5 Flash + Tavily  (parallel per stay)
      │  reduce
      ▼
 [compile_itinerary]  ← Gemini 2.5 Flash
      │
  SSE stream → client
```

Barrier nodes `fanout_travel` and `fanout_activities` act as synchronisation points after their respective parallel fan-outs complete, before dispatching the next wave.

### Model Assignments

| Node | Model | Rationale |
|---|---|---|
| `plan_stays` | `gemini-2.5-pro` | Hardest task: infer sub-destinations, day allocation, cultural fit |
| `plan_activities` | `gemini-2.5-flash` | Timing/geography reasoning per stay |
| `compile_itinerary` | `gemini-2.5-flash` | Structured assembly + budget math |
| `research_stay` | `gemini-2.5-flash-lite` | Structured HTTP tool call → listings service |
| `plan_travel` | `gemini-2.5-flash-lite` | Airport resolution + HTTP tool call → travel service |

---

## API

```
POST /itinerary
Content-Type: application/json
Accept: text/event-stream

{
  "destination": "Italy",
  "start_date": "2025-07-01",
  "end_date": "2025-07-11",
  "adults": 2,
  "children": 0,
  "budget": 5000.0,
  "trip_type": "sightseeing"
}
```

### SSE Event Stream

```
data: {"event": "status", "node": "plan_stays", "message": "..."}
data: {"event": "status", "node": "research_stay", "message": "..."}
data: {"event": "status", "node": "plan_travel", "message": "..."}
data: {"event": "status", "node": "plan_activities", "message": "..."}
data: {"event": "status", "node": "compile_itinerary", "message": "..."}
data: {"event": "complete", "itinerary": { ... }}
```

Error mid-stream: `data: {"event": "error", "node": "...", "message": "..."}`

---

## Itinerary JSON Shape

```json
{
  "destination": "Italy",
  "trip_type": "sightseeing",
  "total_nights": 10,
  "group": { "adults": 2, "children": 0 },
  "budget": 5000.0,
  "estimated_cost": 4620.0,
  "budget_warning": null,
  "stays": [
    {
      "location": "Rome",
      "check_in": "2025-07-01",
      "check_out": "2025-07-04",
      "nights": 3,
      "rationale": "...",
      "accommodation_options": [ /* 3 listings */ ],
      "travel_to_next": {
        "destination": "Florence",
        "options": [ /* 3 flight options */ ]
      },
      "days": [
        {
          "date": "2025-07-01",
          "schedule": [
            { "time": "09:00", "name": "Colosseum", "type": "sightseeing",
              "duration_hours": 2.0, "cost_estimate": 20.0, "notes": "..." }
          ]
        }
      ]
    }
  ]
}
```

`travel_to_next` is `null` for the final stay. Budget warning is set when `estimated_cost > budget`.

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | All LLM nodes |
| `TAVILY_API_KEY` | Tavily web search |
| `LISTINGS_SERVICE_URL` | e.g. `http://listings:8000` |
| `TRAVEL_SERVICE_URL` | e.g. `http://travel:8000` |
