from slack_stats.formatting import build_search_query, categorize_channels


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
