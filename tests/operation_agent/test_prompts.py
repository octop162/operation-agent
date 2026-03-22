def test_system_prompt_is_nonempty_string():
    from operation_agent.prompts import SYSTEM_PROMPT

    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 0


def test_system_prompt_contains_key_concepts():
    from operation_agent.prompts import SYSTEM_PROMPT

    # 障害診断エージェントとしての役割が含まれること
    lower = SYSTEM_PROMPT.lower()
    assert any(kw in lower for kw in ["障害", "診断", "incident", "operation_agent"])


def test_system_prompt_contains_diagnostic_flow():
    from operation_agent.prompts import SYSTEM_PROMPT

    # 診断フローのステップが含まれること
    assert "Notion" in SYSTEM_PROMPT
    assert "CloudWatch" in SYSTEM_PROMPT
    assert "Slack" in SYSTEM_PROMPT


def test_system_prompt_contains_output_format():
    from operation_agent.prompts import SYSTEM_PROMPT

    # 出力フォーマットのセクションが含まれること
    assert "影響" in SYSTEM_PROMPT
    assert "対応必要有無" in SYSTEM_PROMPT
    assert "分析結果" in SYSTEM_PROMPT
    assert "クエリ" in SYSTEM_PROMPT


def test_system_prompt_loaded_from_file():
    from pathlib import Path

    # prompt.md ファイルが存在すること
    import operation_agent.prompts as prompts_module

    prompt_md = Path(prompts_module.__file__).parent / "prompt.md"
    assert prompt_md.exists(), "prompt.md が存在しません"
