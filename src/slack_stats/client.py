from __future__ import annotations

import math
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

    def search_message_results(self, query: str) -> tuple[int, list[dict]]:
        """検索結果を全ページ取得し、総数とメッセージ一覧を返す。"""
        cursor: str | None = "*"
        page = 1
        total = 0
        matches: list[dict] = []

        while True:
            pagination = {"cursor": cursor} if cursor is not None else {"page": page}
            resp = self._call(
                "search_messages",
                query=query,
                count=100,
                sort="timestamp",
                sort_dir="desc",
                **pagination,
            )
            messages = resp["messages"]
            total = messages["total"]
            matches.extend(messages.get("matches", []))

            next_cursor = resp.get("response_metadata", {}).get("next_cursor")
            if next_cursor:
                cursor = next_cursor
                continue

            paging = messages.get("paging") or messages.get("pagination") or {}
            page = int(paging.get("page", page))
            pages = min(
                int(
                    paging.get("pages")
                    or paging.get("page_count")
                    or math.ceil(total / 100)
                ),
                100,
            )
            if page < pages:
                cursor = None
                page += 1
                continue
            break

        return total, matches
