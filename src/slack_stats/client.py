from __future__ import annotations

import time
from typing import Any, Iterator

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

ALL_CONVERSATION_TYPES = "public_channel,private_channel,im,mpim"


class SlackStatsClient:
    """Slack Web API の薄いラッパー。レート制限時は自動リトライする。"""

    def __init__(self, token: str):
        self._client = WebClient(token=token)

    def _call(self, method: str, **kwargs: Any) -> dict:
        while True:
            try:
                return getattr(self._client, method)(**kwargs)
            except SlackApiError as e:
                if e.response.status_code == 429:
                    delay = int(e.response.headers.get("Retry-After", 5))
                    time.sleep(delay)
                    continue
                raise

    def whoami(self) -> dict:
        return self._call("auth_test")

    def list_conversations(self, types: str = ALL_CONVERSATION_TYPES) -> Iterator[dict]:
        """自分が参加しているチャンネル/DM を全件取得する。"""
        cursor = None
        while True:
            resp = self._call(
                "users_conversations",
                types=types,
                exclude_archived=True,
                limit=200,
                cursor=cursor,
            )
            yield from resp["channels"]
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

    def search_message_count(self, query: str) -> int:
        """検索クエリにヒットするメッセージの総数を返す(本文は取得しない)。"""
        resp = self._call("search_messages", query=query, count=1)
        return resp["messages"]["total"]
