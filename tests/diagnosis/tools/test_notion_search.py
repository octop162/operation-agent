import json
from unittest.mock import MagicMock, patch

import pytest


def test_notion_search_tool_exists():
    from diagnosis.tools.notion_search import notion_search  # noqa: F401


def test_notion_search_is_strands_tool():
    from strands.tools.decorator import DecoratedFunctionTool

    from diagnosis.tools.notion_search import notion_search

    assert isinstance(notion_search, DecoratedFunctionTool)


def test_notion_search_returns_string_on_success():
    mock_results = {
        "object": "list",
        "results": [
            {
                "object": "page",
                "id": "page-id-1",
                "url": "https://www.notion.so/page-id-1",
                "properties": {"title": {"title": [{"plain_text": "障害対応手順書"}]}},
            }
        ],
        "has_more": False,
    }

    with patch("diagnosis.tools.notion_search.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = mock_results

        from diagnosis.tools.notion_search import notion_search

        result = notion_search(query="障害対応")

    assert isinstance(result, str)
    data = json.loads(result)
    assert data["object"] == "list"
    assert len(data["results"]) == 1


def test_notion_search_passes_query_param():
    mock_results = {"object": "list", "results": [], "has_more": False}

    with patch("diagnosis.tools.notion_search.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = mock_results

        from diagnosis.tools.notion_search import notion_search

        notion_search(query="runbook")

    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["query"] == "runbook"


def test_notion_search_with_filter_type_page():
    mock_results = {"object": "list", "results": [], "has_more": False}

    with patch("diagnosis.tools.notion_search.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = mock_results

        from diagnosis.tools.notion_search import notion_search

        notion_search(query="手順書", filter_type="page")

    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["filter"] == {"value": "page", "property": "object"}


def test_notion_search_with_filter_type_database():
    mock_results = {"object": "list", "results": [], "has_more": False}

    with patch("diagnosis.tools.notion_search.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = mock_results

        from diagnosis.tools.notion_search import notion_search

        notion_search(query="インシデント", filter_type="database")

    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["filter"] == {"value": "database", "property": "object"}


def test_notion_search_without_filter_type():
    mock_results = {"object": "list", "results": [], "has_more": False}

    with patch("diagnosis.tools.notion_search.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = mock_results

        from diagnosis.tools.notion_search import notion_search

        notion_search(query="手順書")

    call_kwargs = mock_client.search.call_args.kwargs
    assert "filter" not in call_kwargs


def test_notion_search_page_size():
    mock_results = {"object": "list", "results": [], "has_more": False}

    with patch("diagnosis.tools.notion_search.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = mock_results

        from diagnosis.tools.notion_search import notion_search

        notion_search(query="障害", page_size=5)

    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["page_size"] == 5


def test_notion_search_uses_token_from_config(monkeypatch):
    monkeypatch.setenv("DIAG_NOTION_API_TOKEN", "secret_test_token")
    mock_results = {"object": "list", "results": [], "has_more": False}

    with patch("diagnosis.tools.notion_search.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = mock_results

        from diagnosis.tools.notion_search import notion_search

        notion_search(query="test")

    mock_client_cls.assert_called_once_with(auth="secret_test_token")


def test_notion_search_raises_on_api_error():

    import httpx
    from notion_client import APIResponseError
    from notion_client.errors import APIErrorCode

    with patch("diagnosis.tools.notion_search.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_headers = httpx.Headers({})
        mock_client.search.side_effect = APIResponseError(
            code=APIErrorCode.Unauthorized,
            status=401,
            message="Unauthorized",
            headers=mock_headers,
            raw_body_text="",
        )

        from diagnosis.tools.notion_search import notion_search

        with pytest.raises(RuntimeError, match="Notion API error"):
            notion_search(query="test")


@pytest.mark.integration
def test_notion_search_integration():
    """実際のNotion APIへのE2Eテスト（DIAG_NOTION_API_TOKEN 必要）"""
    from diagnosis.tools.notion_search import notion_search

    result = notion_search(query="障害", page_size=1)
    assert isinstance(result, str)
    data = json.loads(result)
    assert "results" in data
