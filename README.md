# Operation Agent

障害診断エージェント - Strands Agents SDK + Amazon Bedrock

## ローカルでの動かし方

### 前提条件

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) インストール済み
- AWS 認証情報（Bedrock アクセス権限付き）

### セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/octop162/operation-agent.git
cd operation-agent

# 依存インストール
uv sync --all-extras

# Git hooks のセットアップ
uv run lefthook install
```

### 環境変数

```bash
cp .env.example .env
```

`.env` を編集して必要な値を設定します。最低限 AWS の設定が必要です。

| 変数 | 説明 | デフォルト |
|------|------|-----------|
| `AWS_REGION` | AWS リージョン | `ap-northeast-1` |
| `AWS_PROFILE` | AWS プロファイル名 | `default` |
| `DIAG_MODEL_ID` | 使用する Bedrock モデル ID | `apac.anthropic.claude-sonnet-4-20250514-v1:0` |
| `DIAG_MYSQL_LAMBDA_FUNCTION` | MySQL 参照 Lambda の関数名 | - |
| `NOTION_API_KEY` | Notion 連携用 API キー（任意） | - |
| `NOTION_DATABASE_ID` | Notion データベース ID（任意） | - |
| `SLACK_BOT_TOKEN` | Slack Bot トークン（任意） | - |
| `SLACK_SIGNING_SECRET` | Slack 署名シークレット（任意） | - |
| `DIAG_OTEL_ENABLED` | OpenTelemetry 有効化（任意） | `false` |
| `DIAG_OTEL_EXPORTER` | OTel エクスポーター種別: `console` \| `otlp`（任意） | `console` |
| `OTEL_SERVICE_NAME` | OTel サービス名（任意） | `operation-agent` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP エンドポイント（任意、`otlp` 時のみ） | `http://localhost:4317` |

### エージェントの起動

```bash
uv run python sample.py
```

> **Note**: `src/` 配下のパッケージを使用するため、必ず `uv run` 経由で実行してください。

### テスト実行

```bash
# ユニットテスト（AWS 不要）
uv run pytest tests/

# 統合テスト（AWS 認証必要）
uv run pytest tests/ -m integration
```

### その他コマンド

```bash
uv run ruff check src/     # lint
uv run ruff format src/    # format
```

## インフラのデプロイ (AWS CDK)

`infra/` ディレクトリに Python CDK プロジェクトがあります。

### 前提条件

- [Node.js](https://nodejs.org/) 18+（CDK CLI のために必要）
- AWS CDK CLI: `npm install -g aws-cdk`
- CDK をデプロイするための IAM 権限（`iam:CreateServiceLinkedRole` 含む）

### デプロイ（推奨）

```bash
# dev 環境
./scripts/deploy.sh dev

# prod 環境
./scripts/deploy.sh prod
```

`scripts/deploy.sh` は CDK 依存インストール・ビルド・ECR プッシュ・AgentCore Runtime 作成を一括で実行します。

### Bootstrap（初回のみ）

```bash
cdk bootstrap aws://ACCOUNT_ID/ap-northeast-1
```

### 個別 CDK コマンド

```bash
cd infra
uv pip install -r requirements.txt

# dev 環境
npx aws-cdk deploy --context env=dev

# prod 環境
npx aws-cdk deploy --context env=prod
```

### 事前準備（SSM パラメータ）

デプロイ前に以下の SSM パラメータを手動で作成してください。

| パラメータ | 説明 |
|---|---|
| `/operation-agent/{env}/mysql-lambda-arn` | MySQL 参照 Lambda の ARN |

### テンプレート生成（デプロイなし）

```bash
cdk synth --context env=dev
```

### 削除

```bash
cdk destroy --context env=dev
```

## Slack Bot のセットアップ

### 1. Slack App の作成

1. [api.slack.com/apps](https://api.slack.com/apps) を開き "Create New App" → "From an app manifest" を選択
2. `slack_app_manifest.json` の内容を貼り付けてアプリを作成
3. "Install to Workspace" でワークスペースにインストール

### 2. トークンの取得

| 項目 | 場所 |
|------|------|
| Bot Token (`xoxb-...`) | "OAuth & Permissions" → "Bot User OAuth Token" |
| Signing Secret | "Basic Information" → "App Credentials" → "Signing Secret" |

### 3. SSM パラメータの登録

```bash
ENV=dev  # または prod

aws ssm put-parameter \
  --name "/operation-agent/${ENV}/slack/bot-token" \
  --type SecureString \
  --value "xoxb-xxxxxxxxxxxx"

aws ssm put-parameter \
  --name "/operation-agent/${ENV}/slack/signing-secret" \
  --type SecureString \
  --value "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 4. SlackBotStack のデプロイ

```bash
./scripts/deploy_slack.sh
```

デプロイ後、出力の `SlackEndpointUrl` をメモします。

### 6. Slack App に URL を設定

1. "Event Subscriptions" を開き "Enable Events" をオン
2. "Request URL" に `SlackEndpointUrl` を入力（Verified と表示されれば OK）
3. "Subscribe to bot events" に `app_mention` が追加されていることを確認
4. "Save Changes" → "Reinstall to Workspace"

### 確認

ボットをチャンネルに招待して `@<ボット名> DBが重い` などとメンションすると、スレッドに「調査中...」が投稿され、診断結果に更新されます。
