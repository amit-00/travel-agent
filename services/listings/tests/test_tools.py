from unittest.mock import MagicMock, patch

import pytest
from listings.tools import search_pexels_image

MP = pytest.MonkeyPatch

PHOTO = {"src": {"large": "https://images.pexels.com/photos/123/photo.jpg"}}
_PEXELS_GET = "listings.tools.httpx.get"


def _mock_response(photos: list[dict]) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {"photos": photos}
    resp.raise_for_status.return_value = None
    return resp


def test_pexels_returns_large_url_on_hit(monkeypatch: MP) -> None:
    monkeypatch.setenv("PEXELS_API_KEY", "test-key")
    with patch(_PEXELS_GET, return_value=_mock_response([PHOTO])):
        url = search_pexels_image.invoke({"query": "cabin mountain"})
    assert url == "https://images.pexels.com/photos/123/photo.jpg"


def test_pexels_sends_api_key_as_auth_header(monkeypatch: MP) -> None:
    monkeypatch.setenv("PEXELS_API_KEY", "my-secret-key")
    mock = _mock_response([PHOTO])
    with patch(_PEXELS_GET, return_value=mock) as mock_get:
        search_pexels_image.invoke({"query": "cabin mountain"})
    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["Authorization"] == "my-secret-key"


def test_pexels_returns_fallback_when_no_results(monkeypatch: MP) -> None:
    monkeypatch.setenv("PEXELS_API_KEY", "test-key")
    with patch(_PEXELS_GET, return_value=_mock_response([])):
        url = search_pexels_image.invoke({"query": "cabin mountain"})
    assert url.startswith("https://")


def test_pexels_raises_when_api_key_missing(monkeypatch: MP) -> None:
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="PEXELS_API_KEY"):
        search_pexels_image.invoke({"query": "cabin mountain"})
