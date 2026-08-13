# slack-stats

Slack での自分の発言数・参加チャンネル数などを調べる CLI ツールです。

- 発言数(全体 / 期間指定 / 会話種別別の件数・割合 / チャンネル別)
- 参加チャンネル数(パブリック / プライベート / DM / グループDM の件数・割合)
- 発言数の多いチャンネル ランキング(任意)

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
# 表示例: 発言数(2026-01-01~2026-07-01)
slack-stats messages --since 2026-01-01 --until 2026-07-01

# 発言数をパブリック / プライベート / DM / グループDM別に表示
# (検索結果をページ送りするため、合計だけの表示より時間がかかります)
slack-stats messages --since 2026-01-01 --breakdown

# 発言数・参加チャンネル数をまとめて表示
slack-stats summary

# 発言数の会話種別別の内訳もまとめて表示
slack-stats summary --since 2026-01-01 --breakdown

# 発言数の多いチャンネル上位5件をパブリック/プライベートの種別付きで表示
# (期間内の検索結果をまとめて取得し、チャンネル別に集計します)
slack-stats summary --since 2026-01-01 --top 5
```

## 開発

```bash
pip install -e ".[dev]"
pytest
```

## 注意事項

- `search.messages` は Slack のレート制限が厳しめです。`--breakdown` / `--top` は検索結果を100件ずつ取得するため、発言数が多い期間では時間がかかる場合があります(自動でリトライします)。
- `search.messages` の従来ページ方式では最大10,000件まで取得できます。それを超える場合は警告を表示するため、`--since` / `--until` で期間を狭めてください。
- `after:` / `before:` は指定日を含まない検索になります(Slack 検索構文の仕様)。
