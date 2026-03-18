import json
from unittest.mock import MagicMock, patch

import pytest


def test_cwl_insights_tool_exists():
    from diagnosis.tools.cwl_insights import cwl_insights  # noqa: F401


def test_cwl_insights_is_strands_tool():
    from strands.tools.decorator import DecoratedFunctionTool

    from diagnosis.tools.cwl_insights import cwl_insights

    assert isinstance(cwl_insights, DecoratedFunctionTool)


def test_cwl_insights_returns_string_on_success():
    results = [
        [{"field": "@timestamp", "value": "2024-01-01 00:00:00.000"}, {"field": "@message", "value": "ERROR foo"}]
    ]

    with patch("diagnosis.tools.cwl_insights.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.start_query.return_value = {"queryId": "abc-123"}
        mock_client.get_query_results.return_value = {"status": "Complete", "results": results, "statistics": {}}

        from diagnosis.tools.cwl_insights import cwl_insights

        result = cwl_insights(
            log_group_names=["/aws/lambda/my-func"],
            query_string="fields @timestamp, @message | limit 10",
            start_time=1700000000,
            end_time=1700003600,
        )

    assert isinstance(result, str)
    data = json.loads(result)
    assert data["status"] == "Complete"
    assert len(data["results"]) == 1


def test_cwl_insights_polls_until_complete():
    results = [[{"field": "@message", "value": "OK"}]]

    with (
        patch("diagnosis.tools.cwl_insights.boto3.client") as mock_boto,
        patch("diagnosis.tools.cwl_insights.time.sleep") as mock_sleep,
    ):
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.start_query.return_value = {"queryId": "xyz-456"}
        mock_client.get_query_results.side_effect = [
            {"status": "Running", "results": []},
            {"status": "Running", "results": []},
            {"status": "Complete", "results": results, "statistics": {}},
        ]

        from diagnosis.tools.cwl_insights import cwl_insights

        result = cwl_insights(
            log_group_names=["/aws/lambda/my-func"],
            query_string="fields @message",
            start_time=1700000000,
            end_time=1700003600,
        )

    assert json.loads(result)["status"] == "Complete"
    assert mock_client.get_query_results.call_count == 3
    assert mock_sleep.call_count == 2


def test_cwl_insights_raises_on_query_failed():
    with (
        patch("diagnosis.tools.cwl_insights.boto3.client") as mock_boto,
        patch("diagnosis.tools.cwl_insights.time.sleep"),
    ):
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.start_query.return_value = {"queryId": "fail-999"}
        mock_client.get_query_results.return_value = {"status": "Failed", "results": []}

        from diagnosis.tools.cwl_insights import cwl_insights

        with pytest.raises(RuntimeError, match="Failed"):
            cwl_insights(
                log_group_names=["/aws/lambda/my-func"],
                query_string="fields @message",
                start_time=1700000000,
                end_time=1700003600,
            )


def test_cwl_insights_raises_on_timeout():
    with (
        patch("diagnosis.tools.cwl_insights.boto3.client") as mock_boto,
        patch("diagnosis.tools.cwl_insights.time.sleep"),
        patch("diagnosis.tools.cwl_insights._POLL_MAX_ATTEMPTS", 3),
    ):
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.start_query.return_value = {"queryId": "slow-000"}
        mock_client.get_query_results.return_value = {"status": "Running", "results": []}

        from diagnosis.tools.cwl_insights import cwl_insights

        with pytest.raises(RuntimeError, match="[Tt]imeout"):
            cwl_insights(
                log_group_names=["/aws/lambda/my-func"],
                query_string="fields @message",
                start_time=1700000000,
                end_time=1700003600,
            )


def test_cwl_insights_raises_on_boto_client_error():
    from botocore.exceptions import ClientError

    error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}

    with patch("diagnosis.tools.cwl_insights.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.start_query.side_effect = ClientError(error_response, "StartQuery")

        from diagnosis.tools.cwl_insights import cwl_insights

        with pytest.raises(RuntimeError, match="Access denied"):
            cwl_insights(
                log_group_names=["/aws/lambda/my-func"],
                query_string="fields @message",
                start_time=1700000000,
                end_time=1700003600,
            )


def test_cwl_insights_passes_correct_params():
    results = [[{"field": "@message", "value": "hello"}]]

    with (
        patch("diagnosis.tools.cwl_insights.boto3.client") as mock_boto,
        patch("diagnosis.tools.cwl_insights.time.sleep"),
    ):
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.start_query.return_value = {"queryId": "param-test"}
        mock_client.get_query_results.return_value = {"status": "Complete", "results": results, "statistics": {}}

        from diagnosis.tools.cwl_insights import cwl_insights

        cwl_insights(
            log_group_names=["/aws/lambda/func-a", "/aws/lambda/func-b"],
            query_string="fields @message | filter @message like /ERROR/",
            start_time=1700000000,
            end_time=1700003600,
            limit=50,
        )

    call_kwargs = mock_client.start_query.call_args.kwargs
    assert call_kwargs["logGroupNames"] == ["/aws/lambda/func-a", "/aws/lambda/func-b"]
    assert call_kwargs["queryString"] == "fields @message | filter @message like /ERROR/"
    assert call_kwargs["startTime"] == 1700000000
    assert call_kwargs["endTime"] == 1700003600
    assert call_kwargs["limit"] == 50


def test_cwl_insights_uses_region_from_config(monkeypatch):
    monkeypatch.setenv("DIAG_AWS_REGION", "us-west-2")
    results = [[{"field": "@message", "value": "ok"}]]

    with (
        patch("diagnosis.tools.cwl_insights.boto3.client") as mock_boto,
        patch("diagnosis.tools.cwl_insights.time.sleep"),
    ):
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.start_query.return_value = {"queryId": "region-test"}
        mock_client.get_query_results.return_value = {"status": "Complete", "results": results, "statistics": {}}

        from diagnosis.tools.cwl_insights import cwl_insights

        cwl_insights(
            log_group_names=["/aws/lambda/my-func"],
            query_string="fields @message",
            start_time=1700000000,
            end_time=1700003600,
        )

    mock_boto.assert_called_once_with("logs", region_name="us-west-2")


def test_cwl_insights_rejects_millisecond_timestamps():
    """ミリ秒タイムスタンプ（13桁）を渡した場合にValueErrorを送出する"""
    from diagnosis.tools.cwl_insights import cwl_insights

    # 現在時刻のミリ秒タイムスタンプ（13桁）
    start_ms = 1700000000000
    end_ms = 1700003600000

    with pytest.raises(ValueError, match="[Uu]nix秒|seconds|timestamp"):
        cwl_insights(
            log_group_names=["/aws/lambda/my-func"],
            query_string="fields @message",
            start_time=start_ms,
            end_time=end_ms,
        )


def test_cwl_insights_rejects_end_before_start():
    """end_time が start_time より前の場合に ValueError を送出する"""
    from diagnosis.tools.cwl_insights import cwl_insights

    with pytest.raises(ValueError, match="end_time|start_time"):
        cwl_insights(
            log_group_names=["/aws/lambda/my-func"],
            query_string="fields @message",
            start_time=1700003600,
            end_time=1700000000,
        )


@pytest.mark.integration
def test_cwl_insights_integration():
    """実際のAWS CloudWatch Logs InsightsへのE2Eテスト（AWS認証必要）"""
    import time

    from diagnosis.tools.cwl_insights import cwl_insights

    end = int(time.time())
    start = end - 3600

    result = cwl_insights(
        log_group_names=["/aws/lambda/health-check"],
        query_string="fields @timestamp, @message | limit 1",
        start_time=start,
        end_time=end,
    )
    assert isinstance(result, str)
    data = json.loads(result)
    assert "status" in data
    assert data["status"] == "Complete"
