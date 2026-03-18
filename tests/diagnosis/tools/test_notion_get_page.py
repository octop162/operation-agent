import json
from unittest.mock import MagicMock, patch

import pytest


def test_notion_get_page_tool_exists():
    from diagnosis.tools.notion_get_page import notion_get_page  # noqa: F401


def test_notion_get_page_is_strands_tool():
    from diagnosis.tools.notion_get_page import notion_get_page
    from strands.tools.decorator import DecoratedFunctionTool

    assert isinstance(notion_get_page, DecoratedFunctionTool)


def test_notion_get_page_returns_string_on_success():
    mock_blocks = {
        "object": "list",
        "results": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"plain_text": "障害対応の手順です。"}],
                },
            }
        ],
        "has_more": False,
        "next_cursor": None,
    }

    with patch("diagnosis.tools.notion_get_page.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.blocks.children.list.return_value = mock_blocks

        from diagnosis.tools.notion_get_page import notion_get_page

        result = notion_get_page(page_id="page-id-1")

    assert isinstance(result, str)
    data = json.loads(result)
    assert data["object"] == "list"
    assert len(data["results"]) == 1


def test_notion_get_page_passes_page_id():
    mock_blocks = {"object": "list", "results": [], "has_more": False, "next_cursor": None}

    with patch("diagnosis.tools.notion_get_page.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.blocks.children.list.return_value = mock_blocks

        from diagnosis.tools.notion_get_page import notion_get_page

        notion_get_page(page_id="abc-123")

    call_kwargs = mock_client.blocks.children.list.call_args.kwargs
    assert call_kwargs["block_id"] == "abc-123"


def test_notion_get_page_passes_page_size():
    mock_blocks = {"object": "list", "results": [], "has_more": False, "next_cursor": None}

    with patch("diagnosis.tools.notion_get_page.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.blocks.children.list.return_value = mock_blocks

        from diagnosis.tools.notion_get_page import notion_get_page

        notion_get_page(page_id="abc-123", page_size=50)

    call_kwargs = mock_client.blocks.children.list.call_args.kwargs
    assert call_kwargs["page_size"] == 50


def test_notion_get_page_uses_token_from_config(monkeypatch):
    monkeypatch.setenv("DIAG_NOTION_API_TOKEN", "secret_test_token")
    mock_blocks = {"object": "list", "results": [], "has_more": False, "next_cursor": None}

    with patch("diagnosis.tools.notion_get_page.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.blocks.children.list.return_value = mock_blocks

        from diagnosis.tools.notion_get_page import notion_get_page

        notion_get_page(page_id="test-id")

    mock_client_cls.assert_called_once_with(auth="secret_test_token")


def test_notion_get_page_raises_on_api_error():
    import httpx
    from notion_client import APIResponseError
    from notion_client.errors import APIErrorCode

    with patch("diagnosis.tools.notion_get_page.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_headers = httpx.Headers({})
        mock_client.blocks.children.list.side_effect = APIResponseError(
            code=APIErrorCode.ObjectNotFound,
            status=404,
            message="Could not find block",
            headers=mock_headers,
            raw_body_text="",
        )

        from diagnosis.tools.notion_get_page import notion_get_page

        with pytest.raises(RuntimeError, match="Notion API error"):
            notion_get_page(page_id="nonexistent-id")


@pytest.mark.integration
def test_notion_get_page_integration():
    """実際のNotion APIへのE2Eテスト（DIAG_NOTION_API_TOKEN と有効なpage_id 必要）"""
    import os

    page_id = os.environ.get("DIAG_NOTION_TEST_PAGE_ID", "")
    if not page_id:
        pytest.skip("DIAG_NOTION_TEST_PAGE_ID not set")

    from diagnosis.tools.notion_get_page import notion_get_page

    result = notion_get_page(page_id=page_id)
    assert isinstance(result, str)
    data = json.loads(result)
    assert "results" in data
