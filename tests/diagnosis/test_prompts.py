def test_system_prompt_is_nonempty_string():
    from diagnosis.prompts import SYSTEM_PROMPT

    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 0


def test_system_prompt_contains_key_concepts():
    from diagnosis.prompts import SYSTEM_PROMPT

    # 障害診断エージェントとしての役割が含まれること
    lower = SYSTEM_PROMPT.lower()
    assert any(kw in lower for kw in ["障害", "診断", "incident", "diagnosis"])
