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
| `BEDROCK_MODEL_ID` | 使用する Bedrock モデル ID | `us.anthropic.claude-sonnet-4-20250514` |
| `NOTION_API_KEY` | Notion 連携用 API キー（任意） | - |
| `NOTION_DATABASE_ID` | Notion データベース ID（任意） | - |
| `SLACK_BOT_TOKEN` | Slack Bot トークン（任意） | - |
| `SLACK_SIGNING_SECRET` | Slack 署名シークレット（任意） | - |

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

### セットアップ

```bash
cd infra
pip install -r requirements.txt
```

### Bootstrap（初回のみ）

```bash
cdk bootstrap aws://ACCOUNT_ID/ap-northeast-1
```

### デプロイ

```bash
# dev 環境
cdk deploy --context env=dev

# prod 環境
cdk deploy --context env=prod
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
