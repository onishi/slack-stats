# slack-stats

Slack での自分の発言数・参加チャンネル数などを調べる CLI ツールです。

- 発言数(全体 / 期間指定 / チャンネル別)
- 参加チャンネル数(パブリック / プライベート / DM / グループDM の内訳)
- 発言数の多いチャンネル ランキング(任意)
- 曜日別・時間帯別の発言傾向

## セットアップ

### 1. Slack App の作成とトークン取得

発言数の集計に Slack の検索 API (`search.messages`) を使用するため、**User OAuth Token** (`xoxp-` から始まるトークン) が必要です。Bot トークンでは検索 API は利用できません。

1. https://api.slack.com/apps で新しい App を作成(対象ワークスペースを選択)
2. "OAuth & Permissions" ページで **User Token Scopes** に以下を追加
   - `search:read`
   - `channels:read`
   - `groups:read`
   - `mpim:read`
   - `im:read`
3. ワークスペースに App をインストールし、発行された `xoxp-...` トークンを控える

### 2. インストール

```bash
pip install -e .
```

### 3. トークンの設定

```bash
cp .env.example .env
# .env を編集して SLACK_USER_TOKEN=xoxp-... を設定
```

環境変数 `SLACK_USER_TOKEN` を直接設定してもかまいません。

## 使い方

```bash
# トークンに紐づくユーザーを確認
slack-stats whoami

# 参加チャンネル数の内訳を表示
slack-stats channels

# 発言数を表示(全期間)
slack-stats messages

# 期間を指定して発言数を表示
slack-stats messages --since 2026-01-01 --until 2026-07-01

# 発言数・参加チャンネル数をまとめて表示
slack-stats summary

# 発言数の多いチャンネル上位5件も合わせて表示
# (チャンネル数だけ検索APIを呼ぶため、チャンネル数が多いと時間がかかります)
slack-stats summary --top 5

# 曜日別・時間帯別の発言傾向を表示(直近1000件を対象、実行環境のローカルタイムゾーン基準)
slack-stats activity

# 集計対象の件数や期間を指定(0で全件取得)
slack-stats activity --since 2026-01-01 --max-messages 0
```

## 開発

```bash
pip install -e ".[dev]"
pytest
```

## 注意事項

- `search.messages` は Slack のレート制限が厳しめです。`--top` オプションや `activity` コマンド使用時、大規模ワークスペースでは実行に時間がかかる場合があります(自動でリトライします)。
- `after:` / `before:` は指定日を含まない検索になります(Slack 検索構文の仕様)。
- `activity` コマンドの曜日・時間帯は実行環境のローカルタイムゾーンで集計されます。
