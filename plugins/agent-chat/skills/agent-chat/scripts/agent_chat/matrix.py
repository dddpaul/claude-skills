"""A small Matrix client-server API client on the standard library.

The access token lives in this process only: it goes into the Authorization
header and never onto a command line. With ``HTTPS_PROXY`` set, every request
goes through the proxy as ``CONNECT <host>:<port>`` and the homeserver's name is
never resolved locally: the proxy's far end resolves it.
"""

from __future__ import annotations

import base64
import http.client
import json
import os
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import quote, urlencode, urlsplit

from .config import AgentChatError

API = "/_matrix/client/v3"
# The relations endpoint exists only under v1.
API_V1 = "/_matrix/client/v1"
# Network failures and 5xx/429 answers are retried, the pause doubling from
# BACKOFF_FIRST up to BACKOFF_MAX, as long as the caller's deadline allows.
BACKOFF_FIRST = 1.0
BACKOFF_MAX = 30.0
# A socket waits this much longer than the request's own long-poll timeout.
SOCKET_SLACK = 10.0
# How many of a thread's newest events a lookup reads.
THREAD_WINDOW = 50


class MatrixError(AgentChatError):
    """The homeserver refused a request."""

    def __init__(self, status: int, errcode: str, error: str) -> None:
        super().__init__(f"homeserver answered {status} {errcode}: {error}".strip())
        self.status = status
        self.errcode = errcode


class AuthError(MatrixError):
    """A 401: the token is wrong, expired or revoked."""


class NetworkError(AgentChatError):
    """The homeserver could not be reached before the deadline."""


def proxy_url(env: Mapping[str, str]) -> str | None:
    """Return the proxy from ``HTTPS_PROXY`` or ``https_proxy``, if any."""
    return env.get("HTTPS_PROXY") or env.get("https_proxy") or None


class Client:
    """One account's connection to the homeserver.

    Args:
        homeserver: The base URL, ``https://<name>``.
        token: The account's access token.
        env: Where to look for the proxy; defaults to the process environment.
        sleep: The pause between retries, overridable for tests.
        now: A monotonic clock, overridable for tests.

    Attributes:
        keep_going: Asked before each retry; a wait sets it to "my Claude
            lives", so a network outage does not keep an orphaned wait alive.
    """

    def __init__(
        self,
        homeserver: str,
        token: str,
        env: Mapping[str, str] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url = urlsplit(homeserver)
        if self._url.scheme not in ("https", "http") or not self._url.hostname:
            raise AgentChatError(f"bad homeserver URL {homeserver!r}", 2)
        self._token = token
        self._proxy = proxy_url(os.environ if env is None else env)
        self._sleep = sleep
        self._now = now
        self.keep_going: Callable[[], bool] = lambda: True

    def _connection(self, timeout: float) -> http.client.HTTPConnection:
        https = self._url.scheme == "https"
        host = self._url.hostname or ""
        port = self._url.port or (443 if https else 80)
        cls = http.client.HTTPSConnection if https else http.client.HTTPConnection
        if not self._proxy:
            return cls(host, port, timeout=timeout)
        p = urlsplit(self._proxy if "://" in self._proxy else f"http://{self._proxy}")
        conn = cls(p.hostname or "", p.port or 1080, timeout=timeout)
        headers = {}
        if p.username:
            cred = f"{p.username}:{p.password or ''}".encode()
            headers["Proxy-Authorization"] = "Basic " + base64.b64encode(cred).decode()
        conn.set_tunnel(host, port, headers)
        return conn

    def _once(
        self, method: str, path: str, body: bytes | None, timeout: float
    ) -> tuple[int, dict[str, Any]]:
        conn = self._connection(timeout)
        try:
            headers = {"Authorization": f"Bearer {self._token}"}
            if body is not None:
                headers["Content-Type"] = "application/json"
            conn.request(method, self._url.path.rstrip("/") + path, body, headers)
            resp = conn.getresponse()
            raw = resp.read()
        finally:
            conn.close()
        try:
            data = json.loads(raw) if raw else {}
        except ValueError:
            data = {}
        return resp.status, data if isinstance(data, dict) else {}

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
        deadline: float | None = None,
        timeout: float = 0.0,
        tries: int | None = None,
    ) -> dict[str, Any]:
        """Send one request, retrying network failures until ``deadline``.

        Args:
            method: The HTTP method.
            path: The path below the homeserver, starting with ``/_matrix``.
            body: A JSON body, if any.
            query: Query parameters, if any.
            deadline: A ``now()`` value after which no retry starts.
            timeout: The request's own long-poll time in seconds.
            tries: When set, the bounded mode: at most this many tries, and
                no socket waits past ``deadline``.

        Raises:
            AuthError: On a 401.
            MatrixError: On any other 4xx.
            NetworkError: When the deadline passes without an answer.
        """
        if query:
            path = f"{path}?{urlencode(query)}"
        data = None if body is None else json.dumps(body).encode()
        pause = BACKOFF_FIRST
        tried = 0
        while True:
            wait = timeout + SOCKET_SLACK
            if tries is not None:
                left = (deadline if deadline is not None else 0.0) - self._now()
                if left <= 0:
                    raise NetworkError("homeserver unreachable (no time left)")
                wait = min(wait, left)
            tried += 1
            try:
                status, answer = self._once(method, path, data, wait)
            except (OSError, http.client.HTTPException) as exc:
                status, answer, why = 0, {}, f"{type(exc).__name__}: {exc}"
            else:
                why = f"HTTP {status}"
            if 200 <= status < 300:
                return answer
            errcode, error = (
                str(answer.get("errcode", "")),
                str(answer.get("error", "")),
            )
            if status == 401:
                raise AuthError(status, errcode, error)
            if 400 <= status < 500 and status != 429:
                raise MatrixError(status, errcode, error)
            if status == 429 and isinstance(answer.get("retry_after_ms"), int):
                pause = min(max(pause, answer["retry_after_ms"] / 1000), BACKOFF_MAX)
            late = deadline is None or self._now() + pause > deadline
            if tries is not None and tried >= tries:
                late = True
            if late or not self.keep_going():
                raise NetworkError(f"homeserver unreachable ({why})")
            if not self._pause(pause):
                raise NetworkError(f"homeserver unreachable ({why}); retries stopped")
            pause = min(pause * 2, BACKOFF_MAX)

    def _pause(self, seconds: float) -> bool:
        """Sleep ``seconds`` in slices of at most one; False once keep_going says no."""
        end = self._now() + seconds
        while (left := end - self._now()) > 0:
            self._sleep(min(left, 1.0))
            if not self.keep_going():
                return False
        return True

    def resolve_alias(self, alias: str, deadline: float) -> str | None:
        """Return the room ID behind ``alias``, or None when it does not resolve."""
        try:
            got = self.request(
                "GET",
                f"{API}/directory/room/{quote(alias, safe='')}",
                deadline=deadline,
            )
        except MatrixError as exc:
            if exc.status == 404 or exc.errcode == "M_NOT_FOUND":
                return None
            raise
        return str(got["room_id"]) if "room_id" in got else None

    def joined_rooms(self, deadline: float) -> set[str]:
        """Return the IDs of the rooms this account has joined."""
        got = self.request("GET", f"{API}/joined_rooms", deadline=deadline)
        return set(got.get("joined_rooms", []))

    def canonical_alias(self, room_id: str, deadline: float) -> str | None:
        """Return the canonical alias of a joined room, or None when it has none."""
        try:
            got = self.request(
                "GET",
                f"{API}/rooms/{quote(room_id, safe='')}/state/m.room.canonical_alias",
                deadline=deadline,
            )
        except MatrixError as exc:
            if exc.status == 404 or exc.errcode == "M_NOT_FOUND":
                return None
            raise
        alias = got.get("alias")
        return alias if isinstance(alias, str) and alias else None

    def join(self, alias: str, deadline: float) -> str:
        """Join the room behind ``alias`` (the account must be invited)."""
        got = self.request(
            "POST", f"{API}/join/{quote(alias, safe='')}", {}, deadline=deadline
        )
        return str(got.get("room_id", ""))

    def create_filter(
        self, user_id: str, definition: dict[str, Any], deadline: float
    ) -> str:
        """Register a sync filter for ``user_id`` and return its ID."""
        got = self.request(
            "POST",
            f"{API}/user/{quote(user_id, safe='')}/filter",
            definition,
            deadline=deadline,
        )
        return str(got["filter_id"])

    def sync(
        self, since: str | None, filt: str, seconds: float, deadline: float
    ) -> dict[str, Any]:
        """Long-poll ``/sync`` for at most ``seconds``."""
        query = {"filter": filt, "timeout": str(int(seconds * 1000))}
        if since:
            query["since"] = since
        return self.request(
            "GET", f"{API}/sync", query=query, deadline=deadline, timeout=seconds
        )

    def send_message(
        self, room_id: str, txn: str, content: dict[str, Any], deadline: float
    ) -> str:
        """Post ``content`` as ``m.room.message``; a retry reuses ``txn``."""
        got = self.request(
            "PUT",
            f"{API}/rooms/{quote(room_id, safe='')}/send/m.room.message/"
            f"{quote(txn, safe='')}",
            content,
            deadline=deadline,
        )
        return str(got.get("event_id", ""))

    def event(
        self, room_id: str, event_id: str, deadline: float
    ) -> dict[str, Any] | None:
        """Return one event of ``room_id``, or None for an unknown ID."""
        try:
            return self.request(
                "GET",
                f"{API}/rooms/{quote(room_id, safe='')}/event/"
                f"{quote(event_id, safe='')}",
                deadline=deadline,
            )
        except MatrixError as exc:
            if exc.status == 404 or exc.errcode == "M_NOT_FOUND":
                return None
            raise

    def thread_latest(self, room_id: str, root: str, deadline: float) -> str | None:
        """Return the ID of the latest message in ``root``'s thread, or None if none."""
        try:
            got = self.request(
                "GET",
                f"{API_V1}/rooms/{quote(room_id, safe='')}/relations/"
                f"{quote(root, safe='')}/m.thread/m.room.message",
                query={"dir": "b", "limit": "1"},
                deadline=deadline,
            )
        except MatrixError as exc:
            if exc.status != 404 or isinstance(exc, AuthError):
                raise
            # Not a MatrixError: a send must not take it for a rejected room.
            raise AgentChatError(f"thread lookup failed: {exc}") from exc
        chunk = got.get("chunk")
        if isinstance(chunk, list) and chunk and isinstance(chunk[0], dict):
            latest = chunk[0].get("event_id")
            if isinstance(latest, str) and latest:
                return latest
        return None

    def thread(
        self, room_id: str, root: str, deadline: float
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Return ``root`` and the newest thread events under it, newest first.

        Both requests run in the bounded mode: two tries each, and nothing
        waits past ``deadline``.

        Raises:
            AuthError: On a 401.
            AgentChatError: When either request fails.
        """
        room, event = quote(room_id, safe=""), quote(root, safe="")
        got = self.request(
            "GET", f"{API}/rooms/{room}/event/{event}", deadline=deadline, tries=2
        )
        children = self.request(
            "GET",
            f"{API_V1}/rooms/{room}/relations/{event}/m.thread",
            query={"dir": "b", "limit": str(THREAD_WINDOW)},
            deadline=deadline,
            tries=2,
        )
        chunk = children.get("chunk")
        if not isinstance(chunk, list):
            return got, []
        return got, [e for e in chunk if isinstance(e, dict)]
