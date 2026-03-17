import json

from notion_client import APIResponseError, Client
from strands import tool

from diagnosis.config import DiagnosisConfig


@tool
def notion_search(
    query: str,
    filter_type: str | None = None,
    page_size: int = 10,
) -> str:
    """Notionを検索し、ページ・データベースの一覧をJSON文字列で返す。

    Args:
        query: 検索クエリ文字列
        filter_type: 検索対象の絞り込み。"page" または "database"。省略時は両方を検索。
        page_size: 返却する最大件数（デフォルト10、最大100）

    Returns:
        検索結果をJSON文字列として返す。
        {"object": "list", "results": [...], "has_more": bool}
    """
    config = DiagnosisConfig()
    client = Client(auth=config.notion_api_token)

    kwargs: dict = {"query": query, "page_size": page_size}
    if filter_type is not None:
        kwargs["filter"] = {"value": filter_type, "property": "object"}

    try:
        response = client.search(**kwargs)
    except APIResponseError as exc:
        raise RuntimeError(f"Notion API error: {exc}") from exc

    return json.dumps(response, ensure_ascii=False, indent=2)
