from click.testing import CliRunner

from slack_stats import cli


class FakeSlackStatsClient:
    def __init__(self):
        self.search_results_calls = 0

    def whoami(self):
        return {"user": "test-user", "team": "test-team"}

    def list_conversations(self, types):
        return iter([])

    def search_message_results(self, query):
        self.search_results_calls += 1
        return 2, [
            {
                "type": "message",
                "channel": {"id": "C1", "name": "general", "is_private": False},
            },
            {
                "type": "message",
                "channel": {"id": "C1", "name": "general", "is_private": False},
            },
        ]

    def search_message_count(self, query):
        raise AssertionError("内訳とランキングの同時指定では個別の件数検索をしない")


def test_summary_reuses_search_results_for_breakdown_and_top(monkeypatch):
    client = FakeSlackStatsClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)

    result = CliRunner().invoke(
        cli.main,
        ["summary", "--since", "2026-08-01", "--breakdown", "--top", "1"],
    )

    assert result.exit_code == 0
    assert client.search_results_calls == 1
    assert "発言数(2026-08-01~)" in result.output
    assert "#general" in result.output
    assert "パブリック" in result.output
