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
    build_search_query,
    categorize_channels,
    categorize_messages,
    format_percentage,
)

console = Console()

CATEGORY_LABELS = {
    "public_channel": "パブリックチャンネル",
    "private_channel": "プライベートチャンネル",
    "im": "DM",
    "mpim": "グループDM",
}

MESSAGE_CATEGORY_LABELS = {
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
@click.option(
    "--breakdown",
    is_flag=True,
    help="発言数をパブリック/プライベート/DM/グループDM別に表示する",
)
def messages(since: str | None, until: str | None, breakdown: bool) -> None:
    """自分の発言数を表示する。"""
    client = get_client()
    query = build_search_query(since=since, until=until)
    if not breakdown:
        total = client.search_message_count(query)
        console.print(f"発言数: [bold]{total}[/bold] 件  (検索クエリ: {query})")
        return

    console.print("発言数の内訳を集計中...")
    total, matches = client.search_message_results(query)
    counts = categorize_messages(matches)

    table = Table(title="発言数の内訳")
    table.add_column("種別")
    table.add_column("件数", justify="right")
    table.add_column("割合", justify="right")
    for key, label in MESSAGE_CATEGORY_LABELS.items():
        table.add_row(label, str(counts[key]), format_percentage(counts[key], total))
    if counts["unknown"]:
        table.add_row(
            "判別不能",
            str(counts["unknown"]),
            format_percentage(counts["unknown"], total),
        )
    table.add_row("合計", str(total), format_percentage(total, total), style="bold")
    console.print(table)
    console.print(f"検索クエリ: {query}")
    warn_if_incomplete_breakdown(total, counts)


@main.command()
def channels() -> None:
    """参加チャンネル一覧・種別ごとの件数を表示する。"""
    client = get_client()
    all_channels = list(client.list_conversations(ALL_CONVERSATION_TYPES))
    counts = categorize_channels(all_channels)

    table = Table(title="参加チャンネル数")
    table.add_column("種別")
    table.add_column("件数", justify="right")
    table.add_column("割合", justify="right")
    total = len(all_channels)
    for key, label in CATEGORY_LABELS.items():
        table.add_row(label, str(counts[key]), format_percentage(counts[key], total))
    table.add_row("合計", str(total), format_percentage(total, total), style="bold")
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
@click.option(
    "--breakdown",
    is_flag=True,
    help="発言数をパブリック/プライベート/DM/グループDM別に表示する",
)
def summary(since: str | None, until: str | None, top: int, breakdown: bool) -> None:
    """発言数・参加チャンネル数などをまとめて表示する。"""
    client = get_client()

    who = client.whoami()
    console.print(f"[bold]{who['user']}[/bold] ({who['team']}) の Slack 統計\n")

    all_channels = list(client.list_conversations(ALL_CONVERSATION_TYPES))
    counts = categorize_channels(all_channels)

    query = build_search_query(since=since, until=until)
    message_counts = None
    if breakdown:
        console.print("発言数の内訳を集計中...")
        total_messages, matches = client.search_message_results(query)
        message_counts = categorize_messages(matches)
    else:
        total_messages = client.search_message_count(query)

    channel_total = len(all_channels)
    table = Table()
    table.add_column("項目")
    table.add_column("件数", justify="right")
    table.add_column("割合", justify="right")
    table.add_row(
        "参加チャンネル数(合計)",
        str(channel_total),
        format_percentage(channel_total, channel_total),
    )
    for key, label in CATEGORY_LABELS.items():
        table.add_row(
            f"  {label}",
            str(counts[key]),
            format_percentage(counts[key], channel_total),
        )
    table.add_row(
        "発言数",
        str(total_messages),
        format_percentage(total_messages, total_messages),
    )
    if message_counts is not None:
        for key, label in MESSAGE_CATEGORY_LABELS.items():
            table.add_row(
                f"  {label}",
                str(message_counts[key]),
                format_percentage(message_counts[key], total_messages),
            )
        if message_counts["unknown"]:
            table.add_row(
                "  判別不能",
                str(message_counts["unknown"]),
                format_percentage(message_counts["unknown"], total_messages),
            )
    console.print(table)
    if message_counts is not None:
        warn_if_incomplete_breakdown(total_messages, message_counts)

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


def warn_if_incomplete_breakdown(total: int, counts: dict[str, int]) -> None:
    """API総数と取得できた内訳の合計が異なる場合に警告する。"""
    categorized = sum(counts.values())
    if categorized != total:
        console.print(
            f"[yellow]注意: Slack API上の合計は {total} 件ですが、"
            f"内訳を取得できたのは {categorized} 件です。[/yellow]"
        )


if __name__ == "__main__":
    main()
