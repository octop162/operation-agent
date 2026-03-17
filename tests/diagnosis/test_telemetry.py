from unittest.mock import MagicMock, patch

from diagnosis.config import DiagnosisConfig
from diagnosis.telemetry import setup_telemetry


def test_setup_telemetry_disabled_does_nothing():
    config = DiagnosisConfig(otel_enabled=False)
    with patch("diagnosis.telemetry.StrandsTelemetry") as mock_cls:
        setup_telemetry(config)
    mock_cls.assert_not_called()


def test_setup_telemetry_console_exporter():
    config = DiagnosisConfig(otel_enabled=True, otel_exporter="console")
    mock_telemetry = MagicMock()
    with patch("diagnosis.telemetry.StrandsTelemetry", return_value=mock_telemetry):
        setup_telemetry(config)
    mock_telemetry.setup_console_exporter.assert_called_once()
    mock_telemetry.setup_otlp_exporter.assert_not_called()


def test_setup_telemetry_otlp_exporter():
    config = DiagnosisConfig(otel_enabled=True, otel_exporter="otlp")
    mock_telemetry = MagicMock()
    with patch("diagnosis.telemetry.StrandsTelemetry", return_value=mock_telemetry):
        setup_telemetry(config)
    mock_telemetry.setup_otlp_exporter.assert_called_once()
    mock_telemetry.setup_console_exporter.assert_not_called()


def test_setup_telemetry_default_config():
    with patch("diagnosis.telemetry.StrandsTelemetry") as mock_cls:
        setup_telemetry()
    mock_cls.assert_not_called()
