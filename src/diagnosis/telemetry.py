from strands.telemetry import StrandsTelemetry

from diagnosis.config import DiagnosisConfig


def setup_telemetry(config: DiagnosisConfig | None = None) -> None:
    """OTelトレース設定を初期化する。otel_enabled=Falseの場合は何もしない。"""
    if config is None:
        config = DiagnosisConfig()
    if not config.otel_enabled:
        return
    telemetry = StrandsTelemetry()
    if config.otel_exporter == "otlp":
        telemetry.setup_otlp_exporter()
    else:
        telemetry.setup_console_exporter()
