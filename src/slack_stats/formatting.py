from __future__ import annotations

from datetime import datetime

WEEKDAY_LABELS = ["月", "火", "水", "木", "金", "土", "日"]


def categorize_channels(channels: list[dict]) -> dict[str, int]:
    """チャンネル一覧を種別ごとの件数に集計する。"""
    counts = {"public_channel": 0, "private_channel": 0, "im": 0, "mpim": 0}
    for ch in channels:
        if ch.get("is_im"):
            counts["im"] += 1
        elif ch.get("is_mpim"):
            counts["mpim"] += 1
        elif ch.get("is_private"):
            counts["private_channel"] += 1
        else:
            counts["public_channel"] += 1
    return counts


def build_search_query(
    in_channel: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> str:
    """`from:me` を起点に検索クエリを組み立てる。"""
    parts = ["from:me"]
    if in_channel:
        parts.append(f"in:{in_channel}")
    if since:
        parts.append(f"after:{since}")
    if until:
        parts.append(f"before:{until}")
    return " ".join(parts)


def summarize_activity(matches: list[dict]) -> tuple[dict[str, int], dict[int, int]]:
    """検索結果のメッセージ一覧から曜日別・時間帯別の発言数を集計する(ローカルタイムゾーン基準)。"""
    weekday_counts = {label: 0 for label in WEEKDAY_LABELS}
    hour_counts = {hour: 0 for hour in range(24)}
    for match in matches:
        ts = match.get("ts")
        if not ts:
            continue
        dt = datetime.fromtimestamp(float(ts))
        weekday_counts[WEEKDAY_LABELS[dt.weekday()]] += 1
        hour_counts[dt.hour] += 1
    return weekday_counts, hour_counts


def render_bar(count: int, max_count: int, width: int = 30) -> str:
    """count を max_count に対する比率でブロック文字のバーとして描画する。"""
    if max_count <= 0 or count <= 0:
        return ""
    filled = max(1, round(count / max_count * width))
    return "█" * filled
