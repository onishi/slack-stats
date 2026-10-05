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
    render_bar,
    summarize_activity,
    build_search_query,
    categorize_channels,
    categorize_messages,
    format_message_label,
    format_percentage,
    rank_message_channels,
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

CHANNEL_TYPE_LABELS = {
    "public_channel": "パブリック",
    "private_channel": "プライベート",
}


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
    message_label = format_message_label(since=since, until=until)
    if not breakdown:
        total = client.search_message_count(query)
        console.print(f"{message_label}: [bold]{total}[/bold] 件  (検索クエリ: {query})")
        return

    console.print("発言数の内訳を集計中...")
    total, matches = client.search_message_results(query)
    counts = categorize_messages(matches)

    table = Table(title=f"{message_label}の内訳")
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
    warn_if_incomplete_results(total, len(matches))


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
    help="検索結果を集計し、発言数の多いチャンネルを上位N件表示する",
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
    message_label = format_message_label(since=since, until=until)
    message_counts = None
    matches = None
    if breakdown or top > 0:
        console.print("発言データを集計中...")
        total_messages, matches = client.search_message_results(query)
        if breakdown:
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
        message_label,
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
    if matches is not None:
        warn_if_incomplete_results(total_messages, len(matches))

    if top > 0 and matches is not None:
        results = rank_message_channels(matches)
        top_table = Table(title=f"発言数の多いチャンネル (上位{top}件)")
        top_table.add_column("チャンネル")
        top_table.add_column("種別")
        top_table.add_column("発言数", justify="right")
        for name, channel_type, count in results[:top]:
            top_table.add_row(
                f"#{name}",
                CHANNEL_TYPE_LABELS[channel_type],
                str(count),
            )
        console.print(top_table)


@main.command(
    epilog=(
        "例:\n\n"
        "  slack-stats activity\n\n"
        "  slack-stats activity --since 2026-01-01 --max-messages 0\n"
    )
)
@click.option("--since", help="この日付以降を集計する (YYYY-MM-DD)。指定日を含まない。")
@click.option("--until", help="この日付以前を集計する (YYYY-MM-DD)。指定日を含まない。")
@click.option(
    "--max-messages",
    type=int,
    default=1000,
    help=(
        "集計に使う最大メッセージ数(既定1000件)。0を指定すると全件取得する。"
        " 件数が多いと search.messages のページ取得回数が増え、時間がかかる。"
    ),
)
def activity(since: str | None, until: str | None, max_messages: int) -> None:
    """曜日別・時間帯別の発言傾向をバーチャートで表示する。

    自分の発言を search.messages でページングしながら取得し、各メッセージの
    タイムスタンプから曜日別・時間帯別の件数を集計します。曜日・時間帯は
    実行環境のローカルタイムゾーンで判定されるため、リモート環境で実行する
    場合は結果が想定と異なる場合があります(TZ 環境変数などで調整してください)。
    """
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


def warn_if_incomplete_results(total: int, retrieved: int) -> None:
    """API総数と取得できた検索結果数が異なる場合に警告する。"""
    if retrieved != total:
        console.print(
            f"[yellow]注意: Slack API上の合計は {total} 件ですが、"
            f"集計できたのは {retrieved} 件です。"
            f"正確な内訳・ランキングには期間を狭めてください。[/yellow]"
        )


if __name__ == "__main__":
    main()
