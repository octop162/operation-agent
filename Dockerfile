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

# AgentCore が呼び出すエントリポイント (#7 で HTTP サーバ化)
CMD ["uv", "run", "python", "-m", "diagnosis.agent"]
