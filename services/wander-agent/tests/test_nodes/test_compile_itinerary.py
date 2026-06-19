from datetime import date

import pytest
from wander_agent.state import (
    DaySchedule,
    ScheduleItem,
    Stay,
    StayWithActivities,
    StayWithListings,
    TravelLeg,
    TripRequest,
    WanderState,
)


def _make_state(budget: float = 5000.0) -> WanderState:
    stay_rome = Stay(
        location="Rome",
        airport_code="FCO",
        check_in=date(2025, 7, 1),
        check_out=date(2025, 7, 4),
        rationale="",
    )
    stay_florence = Stay(
        location="Florence",
        airport_code="FLR",
        check_in=date(2025, 7, 4),
        check_out=date(2025, 7, 8),
        rationale="",
    )
    return WanderState(
        request=TripRequest(
            destination="Italy",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 8),
            adults=2,
            children=0,
            budget=budget,
            trip_type="sightseeing",
        ),
        stays=[stay_rome, stay_florence],
        accommodation_results=[
            StayWithListings(
                stay=stay_rome,
                accommodation_options=[
                    {"price_per_night": 100.0},
                    {"price_per_night": 120.0},
                    {"price_per_night": 150.0},
                ],
            ),
            StayWithListings(
                stay=stay_florence,
                accommodation_options=[
                    {"price_per_night": 90.0},
                    {"price_per_night": 110.0},
                    {"price_per_night": 140.0},
                ],
            ),
        ],
        travel_results=[
            TravelLeg(
                from_location="Rome",
                from_airport="FCO",
                to_location="Florence",
                to_airport="FLR",
                options=[
                    {"cost_per_ticket": 80.0},
                    {"cost_per_ticket": 95.0},
                    {"cost_per_ticket": 120.0},
                ],
            )
        ],
        activity_results=[
            StayWithActivities(
                stay=stay_rome,
                days=[
                    DaySchedule(
                        date=date(2025, 7, 1),
                        schedule=[
                            ScheduleItem(
                                time="09:00",
                                name="Colosseum",
                                type="sightseeing",
                                duration_hours=2.0,
                                cost_estimate=20.0,
                                notes="",
                            )
                        ],
                    )
                ],
            ),
            StayWithActivities(
                stay=stay_florence,
                days=[
                    DaySchedule(
                        date=date(2025, 7, 4),
                        schedule=[
                            ScheduleItem(
                                time="10:00",
                                name="Uffizi Gallery",
                                type="sightseeing",
                                duration_hours=2.5,
                                cost_estimate=25.0,
                                notes="",
                            )
                        ],
                    )
                ],
            ),
        ],
        itinerary=None,
    )


@pytest.mark.asyncio
async def test_compile_itinerary_returns_valid_structure() -> None:
    from wander_agent.nodes.compile_itinerary import compile_itinerary

    state = _make_state()
    result = await compile_itinerary(state)

    assert "itinerary" in result
    itinerary = result["itinerary"]
    assert itinerary is not None
    assert itinerary["destination"] == "Italy"
    assert itinerary["trip_type"] == "sightseeing"
    assert len(itinerary["stays"]) == 2  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_compile_itinerary_no_budget_warning_when_under() -> None:
    from wander_agent.nodes.compile_itinerary import compile_itinerary

    state = _make_state(budget=50000.0)
    result = await compile_itinerary(state)

    assert result["itinerary"]["budget_warning"] is None  # type: ignore[index]


@pytest.mark.asyncio
async def test_compile_itinerary_budget_warning_when_over() -> None:
    from wander_agent.nodes.compile_itinerary import compile_itinerary

    state = _make_state(budget=10.0)
    result = await compile_itinerary(state)

    assert result["itinerary"]["budget_warning"] is not None  # type: ignore[index]
    assert "exceeds" in result["itinerary"]["budget_warning"].lower()  # type: ignore[index]


@pytest.mark.asyncio
async def test_compile_itinerary_last_stay_has_no_travel_to_next() -> None:
    from wander_agent.nodes.compile_itinerary import compile_itinerary

    state = _make_state()
    result = await compile_itinerary(state)

    stays = result["itinerary"]["stays"]  # type: ignore[index]
    assert stays[-1]["travel_to_next"] is None
