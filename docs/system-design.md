# Travel Agent — System Design

## Sub-projects

| # | Sub-project | What it does | Depends on |
|---|---|---|---|
| 1 | **Core itinerary generation** | User inputs destination + dates + preferences → LLM agent builds a day-by-day itinerary | Nothing — this is the AI heart |
| 2 | **Accommodation search** | Query travel APIs (hotels, Airbnb-style), rank results, return structured listings | Sub-project 1 (needs trip context) |
| 3 | **Trip planning UI** | Frontend: search input, itinerary display, accommodation cards, map view | Sub-projects 1 + 2 |
| 4 | **User profiles + trip persistence** | Accounts, saved trips, preference history that feeds personalization | Sub-project 3 (gives users something to save) |
| 5 | **Analytics dashboard** | Engagement metrics, recommendation quality monitoring | Sub-project 4 (needs usage data) |
