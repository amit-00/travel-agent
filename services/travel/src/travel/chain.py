from typing import cast

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI

from .models import FlightsPayload

_SYSTEM_PROMPT = """\
You are a flight search engine for a travel app demo. Generate exactly 3 realistic \
one-way flight options that match the search criteria provided.

For each option produce:
- A real airline name (e.g. Delta, United, American Airlines, Southwest, JetBlue, \
  Alaska Airlines, Spirit, Frontier, British Airways, Lufthansa)
- Realistic departure and arrival datetimes consistent with the constraint given
- A realistic economy-class price per ticket in USD ($50–$1500 depending on route)
- 0–2 layovers; each layover uses a valid IATA airport code and a duration of \
  45–180 minutes

Make the 3 options diverse: vary airline, total travel time, price, and routing. \
Direct flights should generally cost more than connecting flights for the same route.\
"""


def build_flights_chain() -> Runnable[dict[str, str], FlightsPayload]:
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
    structured_model = model.with_structured_output(FlightsPayload)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", "{request}"),
        ]
    )
    return cast(Runnable[dict[str, str], FlightsPayload], prompt | structured_model)
