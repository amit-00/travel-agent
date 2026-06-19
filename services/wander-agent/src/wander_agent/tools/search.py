import os

from langchain_tavily import TavilySearch


def build_search_tool() -> TavilySearch:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set")
    return TavilySearch(max_results=5, tavily_api_key=api_key)
