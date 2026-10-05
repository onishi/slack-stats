from slack_stats.client import SlackStatsClient


class FakeWebClient:
    def __init__(self):
        self.calls = []

    def search_messages(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["cursor"] == "*":
            return {
                "messages": {"total": 3, "matches": [{"iid": "1"}, {"iid": "2"}]},
                "response_metadata": {"next_cursor": "next"},
            }
        return {
            "messages": {"total": 3, "matches": [{"iid": "3"}]},
            "response_metadata": {"next_cursor": ""},
        }


class FakePageWebClient:
    def __init__(self):
        self.calls = []

    def search_messages(self, **kwargs):
        self.calls.append(kwargs)
        page = kwargs.get("page", 1)
        return {
            "messages": {
                "total": 3,
                "matches": [{"iid": str(page)}],
                "pagination": {"page": page, "page_count": 3},
            }
        }


def test_search_message_results_follows_cursor_pagination():
    client = SlackStatsClient("xoxp-test")
    fake = FakeWebClient()
    client._client = fake

    total, matches = client.search_message_results("from:me")

    assert total == 3
    assert matches == [{"iid": "1"}, {"iid": "2"}, {"iid": "3"}]
    assert [call["cursor"] for call in fake.calls] == ["*", "next"]
    assert all(call["count"] == 100 for call in fake.calls)


def test_search_message_results_falls_back_to_page_pagination():
    client = SlackStatsClient("xoxp-test")
    fake = FakePageWebClient()
    client._client = fake

    total, matches = client.search_message_results("from:me")

    assert total == 3
    assert matches == [{"iid": "1"}, {"iid": "2"}, {"iid": "3"}]
    assert fake.calls[0]["cursor"] == "*"
    assert [call["page"] for call in fake.calls[1:]] == [2, 3]


def test_search_message_results_calculates_pages_from_total_as_fallback():
    client = SlackStatsClient("xoxp-test")
    fake = FakePageWebClient()
    client._client = fake

    original_search = fake.search_messages

    def search_without_pagination(**kwargs):
        response = original_search(**kwargs)
        response["messages"].pop("pagination")
        response["messages"]["total"] = 201
        return response

    fake.search_messages = search_without_pagination

    total, matches = client.search_message_results("from:me")

    assert total == 201
    assert len(matches) == 3
    assert [call["page"] for call in fake.calls[1:]] == [2, 3]


def test_search_message_results_stops_at_legacy_page_limit():
    client = SlackStatsClient("xoxp-test")
    fake = FakePageWebClient()
    client._client = fake

    original_search = fake.search_messages

    def search_over_page_limit(**kwargs):
        response = original_search(**kwargs)
        response["messages"]["pagination"]["page_count"] = 101
        response["messages"]["total"] = 10_001
        return response

    fake.search_messages = search_over_page_limit

    total, matches = client.search_message_results("from:me")

    assert total == 10_001
    assert len(matches) == 100
    assert fake.calls[-1]["page"] == 100
