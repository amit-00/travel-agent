from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from listings.tools import search_pexels_image

MP = pytest.MonkeyPatch

PHOTO = {"src": {"large": "https://images.pexels.com/photos/123/photo.jpg"}}
_PEXELS_CLIENT = "listings.tools.httpx.AsyncClient"


def _make_client(photos: list[dict]) -> AsyncMock:
    mock_response = MagicMock()
    mock_response.json.return_value = {"photos": photos}
    client = AsyncMock()
    client.get = AsyncMock(return_value=mock_response)
    client.__aenter__ = AsyncMock(return_value=client)
    return client


async def test_pexels_returns_large_url_on_hit(monkeypatch: MP) -> None:
    monkeypatch.setenv("PEXELS_API_KEY", "test-key")
    with patch(_PEXELS_CLIENT, return_value=_make_client([PHOTO])):
        url = await search_pexels_image.ainvoke({"query": "cabin mountain"})
    assert url == "https://images.pexels.com/photos/123/photo.jpg"


async def test_pexels_sends_api_key_as_auth_header(monkeypatch: MP) -> None:
    monkeypatch.setenv("PEXELS_API_KEY", "my-secret-key")
    mock_client = _make_client([PHOTO])
    with patch(_PEXELS_CLIENT, return_value=mock_client):
        await search_pexels_image.ainvoke({"query": "cabin mountain"})
    _, kwargs = mock_client.get.call_args
    assert kwargs["headers"]["Authorization"] == "my-secret-key"


async def test_pexels_returns_fallback_when_no_results(monkeypatch: MP) -> None:
    monkeypatch.setenv("PEXELS_API_KEY", "test-key")
    with patch(_PEXELS_CLIENT, return_value=_make_client([])):
        url = await search_pexels_image.ainvoke({"query": "cabin mountain"})
    assert url.startswith("https://")


async def test_pexels_raises_when_api_key_missing(monkeypatch: MP) -> None:
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="PEXELS_API_KEY"):
        await search_pexels_image.ainvoke({"query": "cabin mountain"})
