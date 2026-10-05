from datetime import datetime

from slack_stats.formatting import (
    render_bar,
    summarize_activity,
    build_search_query,
    categorize_channels,
    categorize_messages,
    format_message_label,
    format_percentage,
    rank_message_channels,
)


def test_format_percentage_with_one_decimal_place():
    assert format_percentage(1, 3) == "33.3%"
    assert format_percentage(3, 4) == "75.0%"


def test_format_percentage_with_zero_total():
    assert format_percentage(0, 0) == "0.0%"


def test_format_message_label_without_dates():
    assert format_message_label() == "発言数"


def test_format_message_label_with_since_only():
    assert format_message_label(since="2026-08-01") == "発言数(2026-08-01~)"


def test_format_message_label_with_until_only():
    assert format_message_label(until="2026-08-13") == "発言数(~2026-08-13)"


def test_format_message_label_with_date_range():
    assert (
        format_message_label(since="2026-08-01", until="2026-08-13")
        == "発言数(2026-08-01~2026-08-13)"
    )


def test_categorize_channels_counts_each_type():
    channels = [
        {"is_private": False},
        {"is_private": False},
        {"is_private": True},
        {"is_im": True},
        {"is_mpim": True},
    ]
    counts = categorize_channels(channels)
    assert counts == {
        "public_channel": 2,
        "private_channel": 1,
        "im": 1,
        "mpim": 1,
    }


def test_categorize_channels_empty_list():
    assert categorize_channels([]) == {
        "public_channel": 0,
        "private_channel": 0,
        "im": 0,
        "mpim": 0,
    }


def test_categorize_messages_counts_each_conversation_type():
    messages = [
        {"type": "message", "channel": {"id": "C1", "is_private": False}},
        {"type": "message", "channel": {"id": "C2", "is_private": True}},
        {"type": "group", "channel": {"id": "G1", "is_private": True}},
        {"type": "im", "channel": {"id": "D1"}},
        {"type": "group", "channel": {"id": "G2", "is_mpim": True}},
        {"type": "message"},
    ]

    assert categorize_messages(messages) == {
        "public_channel": 1,
        "private_channel": 2,
        "im": 1,
        "mpim": 1,
        "unknown": 1,
    }


def test_categorize_messages_empty_list():
    assert categorize_messages([]) == {
        "public_channel": 0,
        "private_channel": 0,
        "im": 0,
        "mpim": 0,
        "unknown": 0,
    }


def test_rank_message_channels_counts_channels_and_excludes_direct_messages():
    messages = [
        {"type": "message", "channel": {"id": "C1", "name": "general"}},
        {"type": "message", "channel": {"id": "C1", "name": "general"}},
        {
            "type": "group",
            "channel": {"id": "G1", "name": "private", "is_private": True},
        },
        {"type": "im", "channel": {"id": "D1", "name": "U1"}},
        {
            "type": "group",
            "channel": {"id": "G2", "name": "mpdm", "is_mpim": True},
        },
        {"type": "message", "channel": {}},
    ]

    assert rank_message_channels(messages) == [
        ("general", "public_channel", 2),
        ("private", "private_channel", 1),
    ]


def test_rank_message_channels_sorts_ties_by_name():
    messages = [
        {"type": "message", "channel": {"id": "C2", "name": "zebra"}},
        {"type": "message", "channel": {"id": "C1", "name": "alpha"}},
    ]

    assert rank_message_channels(messages) == [
        ("alpha", "public_channel", 1),
        ("zebra", "public_channel", 1),
    ]


def test_build_search_query_default_is_from_me():
    assert build_search_query() == "from:me"


def test_build_search_query_with_channel_and_dates():
    query = build_search_query(in_channel="#general", since="2026-01-01", until="2026-07-01")
    assert query == "from:me in:#general after:2026-01-01 before:2026-07-01"

def test_summarize_activity_counts_weekday_and_hour():
    monday_9am_a = datetime(2026, 7, 20, 9, 0, 0)
    monday_9am_b = datetime(2026, 7, 20, 9, 30, 0)
    tuesday_3pm = datetime(2026, 7, 21, 15, 0, 0)
    matches = [
        {"ts": str(monday_9am_a.timestamp())},
        {"ts": str(monday_9am_b.timestamp())},
        {"ts": str(tuesday_3pm.timestamp())},
    ]

    weekday_counts, hour_counts = summarize_activity(matches)

    assert weekday_counts["月"] == 2
    assert weekday_counts["火"] == 1
    assert weekday_counts["水"] == 0
    assert hour_counts[9] == 2
    assert hour_counts[15] == 1
    assert hour_counts[0] == 0


def test_summarize_activity_skips_matches_without_ts():
    weekday_counts, hour_counts = summarize_activity([{}])
    assert sum(weekday_counts.values()) == 0
    assert sum(hour_counts.values()) == 0


def test_render_bar_scales_to_width():
    assert render_bar(5, 10, width=10) == "█████"
    assert render_bar(10, 10, width=10) == "██████████"


def test_render_bar_zero_count_is_empty():
    assert render_bar(0, 10) == ""


def test_render_bar_zero_max_is_empty():
    assert render_bar(3, 0) == ""
