from slack_stats.formatting import (
    build_search_query,
    categorize_channels,
    categorize_messages,
    format_percentage,
)


def test_format_percentage_with_one_decimal_place():
    assert format_percentage(1, 3) == "33.3%"
    assert format_percentage(3, 4) == "75.0%"


def test_format_percentage_with_zero_total():
    assert format_percentage(0, 0) == "0.0%"


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


def test_build_search_query_default_is_from_me():
    assert build_search_query() == "from:me"


def test_build_search_query_with_channel_and_dates():
    query = build_search_query(in_channel="#general", since="2026-01-01", until="2026-07-01")
    assert query == "from:me in:#general after:2026-01-01 before:2026-07-01"
