import json


def test_current_time_tool_exists():
    from diagnosis.tools.current_time import get_current_time  # noqa: F401


def test_current_time_is_strands_tool():
    from diagnosis.tools.current_time import get_current_time
    from strands.tools.decorator import DecoratedFunctionTool

    assert isinstance(get_current_time, DecoratedFunctionTool)


def test_current_time_returns_string():
    from diagnosis.tools.current_time import get_current_time

    result = get_current_time()
    assert isinstance(result, str)


def test_current_time_returns_valid_json():
    from diagnosis.tools.current_time import get_current_time

    result = get_current_time()
    data = json.loads(result)
    assert "unix_seconds" in data
    assert "utc" in data
    assert "jst" in data


def test_current_time_unix_seconds_is_int():
    from diagnosis.tools.current_time import get_current_time

    result = get_current_time()
    data = json.loads(result)
    assert isinstance(data["unix_seconds"], int)


def test_current_time_unix_seconds_is_reasonable():
    """Unix秒が10桁（ミリ秒でない）であることを確認"""
    import time

    from diagnosis.tools.current_time import get_current_time

    before = int(time.time())
    result = get_current_time()
    after = int(time.time())
    data = json.loads(result)

    assert before <= data["unix_seconds"] <= after
    # 10桁であること（ミリ秒の13桁ではない）
    assert len(str(data["unix_seconds"])) == 10


def test_current_time_utc_contains_timezone():
    from diagnosis.tools.current_time import get_current_time

    result = get_current_time()
    data = json.loads(result)
    assert "+00:00" in data["utc"] or "Z" in data["utc"]


def test_current_time_jst_contains_timezone():
    from diagnosis.tools.current_time import get_current_time

    result = get_current_time()
    data = json.loads(result)
    assert "+09:00" in data["jst"]
