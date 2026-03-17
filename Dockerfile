# AgentCore Runtime コンテナ
# ARM64 (linux/arm64) でビルドすること: docker buildx build --platform linux/arm64
FROM python:3.12-slim

WORKDIR /app

# uv でパッケージインストール
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --frozen

# アプリケーションコードをコピー
COPY src/ ./src/

# AgentCore が呼び出すエントリポイント (HTTP サーバ, ポート 8080)
CMD ["uv", "run", "python", "-m", "diagnosis"]
