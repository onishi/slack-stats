from __future__ import annotations


def format_percentage(count: int, total: int) -> str:
    """件数を合計に対する小数1桁の割合へ整形する。"""
    if total == 0:
        return "0.0%"
    return f"{count / total:.1%}"


def format_message_label(since: str | None = None, until: str | None = None) -> str:
    """期間指定を含む発言数の表示名を返す。"""
    if not since and not until:
        return "発言数"
    return f"発言数({since or ''}~{until or ''})"


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


def categorize_messages(messages: list[dict]) -> dict[str, int]:
    """検索結果のメッセージを会話種別ごとの件数に集計する。"""
    counts = {
        "public_channel": 0,
        "private_channel": 0,
        "im": 0,
        "mpim": 0,
        "unknown": 0,
    }
    for message in messages:
        channel = message.get("channel") or {}
        if channel.get("is_mpim"):
            counts["mpim"] += 1
        elif message.get("type") == "im" or channel.get("is_im"):
            counts["im"] += 1
        elif channel.get("is_private") or message.get("type") == "group":
            counts["private_channel"] += 1
        elif channel:
            counts["public_channel"] += 1
        else:
            counts["unknown"] += 1
    return counts


def rank_message_channels(messages: list[dict]) -> list[tuple[str, str, int]]:
    """検索結果をパブリック/プライベートチャンネル別の発言数順に並べる。"""
    channels: dict[str, dict[str, str | int]] = {}
    for message in messages:
        channel = message.get("channel") or {}
        if (
            message.get("type") == "im"
            or channel.get("is_im")
            or channel.get("is_mpim")
        ):
            continue

        name = channel.get("name")
        if not name:
            continue
        key = channel.get("id") or f"name:{name}"
        channel_type = (
            "private_channel"
            if channel.get("is_private") or message.get("type") == "group"
            else "public_channel"
        )
        entry = channels.setdefault(
            key,
            {"name": name, "type": channel_type, "count": 0},
        )
        entry["count"] = int(entry["count"]) + 1

    return sorted(
        [
            (str(entry["name"]), str(entry["type"]), int(entry["count"]))
            for entry in channels.values()
        ],
        key=lambda item: (-item[2], item[0]),
    )


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
