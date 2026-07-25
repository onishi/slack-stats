from __future__ import annotations


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
