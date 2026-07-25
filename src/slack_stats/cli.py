from __future__ import annotations

import os
import sys
import time

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .client import ALL_CONVERSATION_TYPES, SlackStatsClient
from .formatting import (
    WEEKDAY_LABELS,
    build_search_query,
    categorize_channels,
    render_bar,
    summarize_activity,
)

console = Console()

CATEGORY_LABELS = {
    "public_channel": "パブリックチャンネル",
    "private_channel": "プライベートチャンネル",
    "im": "DM",
    "mpim": "グループDM",
}

# search.messages は Slack 側のレート制限が厳しいため、連続呼び出し間に間隔を空ける。
TOP_CHANNEL_QUERY_DELAY_SECONDS = 2.0


def get_client() -> SlackStatsClient:
    load_dotenv()
    token = os.environ.get("SLACK_USER_TOKEN")
    if not token:
        console.print(
            "[red]SLACK_USER_TOKEN が設定されていません。"
            ".env.example を参考に .env を作成するか環境変数を設定してください。[/red]"
        )
        sys.exit(1)
    return SlackStatsClient(token)


@click.group()
def main() -> None:
    """Slack の自分の発言数・参加チャンネル数などを調べる CLI ツール。"""


@main.command()
def whoami() -> None:
    """トークンに紐づくユーザー情報を表示する。"""
    client = get_client()
    info = client.whoami()
    console.print(f"User: [bold]{info['user']}[/bold] ({info['user_id']})  Team: {info['team']}")


@main.command()
@click.option("--since", help="この日付以降を集計 (YYYY-MM-DD)")
@click.option("--until", help="この日付以前を集計 (YYYY-MM-DD)")
def messages(since: str | None, until: str | None) -> None:
    """自分の発言数を表示する。"""
    client = get_client()
    query = build_search_query(since=since, until=until)
    total = client.search_message_count(query)
    console.print(f"発言数: [bold]{total}[/bold] 件  (検索クエリ: {query})")


@main.command()
def channels() -> None:
    """参加チャンネル一覧・種別ごとの件数を表示する。"""
    client = get_client()
    all_channels = list(client.list_conversations(ALL_CONVERSATION_TYPES))
    counts = categorize_channels(all_channels)

    table = Table(title="参加チャンネル数")
    table.add_column("種別")
    table.add_column("件数", justify="right")
    for key, label in CATEGORY_LABELS.items():
        table.add_row(label, str(counts[key]))
    table.add_row("合計", str(len(all_channels)), style="bold")
    console.print(table)


@main.command()
@click.option("--since", help="この日付以降を集計 (YYYY-MM-DD)")
@click.option("--until", help="この日付以前を集計 (YYYY-MM-DD)")
@click.option(
    "--top",
    type=int,
    default=0,
    help="発言数の多いチャンネルを上位N件表示する (チャンネル数分だけAPI呼び出しが増えるため既定は無効)",
)
def summary(since: str | None, until: str | None, top: int) -> None:
    """発言数・参加チャンネル数などをまとめて表示する。"""
    client = get_client()

    who = client.whoami()
    console.print(f"[bold]{who['user']}[/bold] ({who['team']}) の Slack 統計\n")

    all_channels = list(client.list_conversations(ALL_CONVERSATION_TYPES))
    counts = categorize_channels(all_channels)

    query = build_search_query(since=since, until=until)
    total_messages = client.search_message_count(query)

    table = Table(show_header=False)
    table.add_row("参加チャンネル数(合計)", str(len(all_channels)))
    for key, label in CATEGORY_LABELS.items():
        table.add_row(f"  {label}", str(counts[key]))
    table.add_row("発言数", str(total_messages))
    console.print(table)

    if top > 0:
        named_channels = [
            ch
            for ch in all_channels
            if not ch.get("is_im") and not ch.get("is_mpim") and ch.get("name")
        ]
        console.print(
            f"\n発言数の多いチャンネルを集計中... "
            f"({len(named_channels)} チャンネル、レート制限のため時間がかかる場合があります)"
        )
        results = []
        for i, ch in enumerate(named_channels):
            if i > 0:
                time.sleep(TOP_CHANNEL_QUERY_DELAY_SECONDS)
            q = build_search_query(in_channel=f"#{ch['name']}", since=since, until=until)
            count = client.search_message_count(q)
            if count > 0:
                results.append((ch["name"], count))
        results.sort(key=lambda x: x[1], reverse=True)

        top_table = Table(title=f"発言数の多いチャンネル (上位{top}件)")
        top_table.add_column("チャンネル")
        top_table.add_column("発言数", justify="right")
        for name, count in results[:top]:
            top_table.add_row(f"#{name}", str(count))
        console.print(top_table)


@main.command()
@click.option("--since", help="この日付以降を集計 (YYYY-MM-DD)")
@click.option("--until", help="この日付以前を集計 (YYYY-MM-DD)")
@click.option(
    "--max-messages",
    type=int,
    default=1000,
    help="集計に使う最大メッセージ数。0を指定すると全件取得する(件数が多いと時間がかかります)",
)
def activity(since: str | None, until: str | None, max_messages: int) -> None:
    """曜日別・時間帯別の発言傾向を表示する(実行環境のローカルタイムゾーン基準)。"""
    client = get_client()
    query = build_search_query(since=since, until=until)
    limit = None if max_messages == 0 else max_messages

    console.print(f"発言データを取得中... (検索クエリ: {query})")
    matches = list(client.search_messages_iter(query, max_results=limit))
    if not matches:
        console.print("[yellow]該当する発言が見つかりませんでした。[/yellow]")
        return
    console.print(f"{len(matches)} 件のメッセージを集計しました。\n")

    weekday_counts, hour_counts = summarize_activity(matches)

    weekday_table = Table(title="曜日別の発言数")
    weekday_table.add_column("曜日")
    weekday_table.add_column("件数", justify="right")
    weekday_table.add_column("")
    max_weekday = max(weekday_counts.values())
    for label in WEEKDAY_LABELS:
        count = weekday_counts[label]
        weekday_table.add_row(label, str(count), render_bar(count, max_weekday))
    console.print(weekday_table)

    hour_table = Table(title="時間帯別の発言数")
    hour_table.add_column("時")
    hour_table.add_column("件数", justify="right")
    hour_table.add_column("")
    max_hour = max(hour_counts.values())
    for hour in range(24):
        count = hour_counts[hour]
        hour_table.add_row(f"{hour:02d}時", str(count), render_bar(count, max_hour))
    console.print(hour_table)


if __name__ == "__main__":
    main()
