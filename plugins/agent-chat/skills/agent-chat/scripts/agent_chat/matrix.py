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
# Network failures and 5xx/429 answers are retried, the pause doubling from
# BACKOFF_FIRST up to BACKOFF_MAX, as long as the caller's deadline allows.
BACKOFF_FIRST = 1.0
BACKOFF_MAX = 30.0
# A socket waits this much longer than the request's own long-poll timeout.
SOCKET_SLACK = 10.0


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
    ) -> dict[str, Any]:
        """Send one request, retrying network failures until ``deadline``.

        Args:
            method: The HTTP method.
            path: The path below the homeserver, starting with ``/_matrix``.
            body: A JSON body, if any.
            query: Query parameters, if any.
            deadline: A ``now()`` value after which no retry starts.
            timeout: The request's own long-poll time in seconds.

        Raises:
            AuthError: On a 401.
            MatrixError: On any other 4xx.
            NetworkError: When the deadline passes without an answer.
        """
        if query:
            path = f"{path}?{urlencode(query)}"
        data = None if body is None else json.dumps(body).encode()
        pause = BACKOFF_FIRST
        while True:
            try:
                status, answer = self._once(method, path, data, timeout + SOCKET_SLACK)
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
                pause = max(pause, answer["retry_after_ms"] / 1000)
            late = deadline is None or self._now() + pause > deadline
            if late or not self.keep_going():
                raise NetworkError(f"homeserver unreachable ({why})")
            self._sleep(pause)
            pause = min(pause * 2, BACKOFF_MAX)

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
