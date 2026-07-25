from datetime import datetime

from slack_stats.formatting import (
    build_search_query,
    categorize_channels,
    render_bar,
    summarize_activity,
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
