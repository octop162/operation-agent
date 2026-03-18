# AgentCore Runtime コンテナ
# ARM64 (linux/arm64) でビルドすること: docker buildx build --platform linux/arm64
FROM python:3.12-slim

WORKDIR /app

# uv でパッケージインストール
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --frozen

# AgentCore が呼び出すエントリポイント (HTTP サーバ, ポート 8080)
# uv run を避け .venv を直接使うことで起動時の再 sync を防ぐ
CMD ["/app/.venv/bin/opentelemetry-instrument", "/app/.venv/bin/python", "-m", "diagnosis"]
