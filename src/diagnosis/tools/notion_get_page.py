import json

from notion_client import APIResponseError, Client
from strands import tool

from diagnosis.config import DiagnosisConfig


@tool
def notion_get_page(
    page_id: str,
    page_size: int = 100,
) -> str:
    """Notionページのブロック（本文）をJSON文字列で返す。

    Args:
        page_id: 取得対象のNotionページIDまたはブロックID
        page_size: 返却する最大ブロック数（デフォルト100、最大100）

    Returns:
        ページのブロック一覧をJSON文字列として返す。
        {"object": "list", "results": [...], "has_more": bool, "next_cursor": str | None}
    """
    config = DiagnosisConfig()
    client = Client(auth=config.notion_api_token)

    try:
        response = client.blocks.children.list(block_id=page_id, page_size=page_size)
    except APIResponseError as exc:
        raise RuntimeError(f"Notion API error: {exc}") from exc

    return json.dumps(response, ensure_ascii=False, indent=2)
