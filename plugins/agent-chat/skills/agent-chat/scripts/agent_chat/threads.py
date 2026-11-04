"""Thread facts from the homeserver, read within one budget per sync batch.

Nothing about threads is stored: each batch asks the server once per
(room, root) for the root and the thread's newest events, and judges from
them which agents take part. A failed lookup is remembered for the batch, so
it is not asked again; once the budget is spent every lookup fails at once.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .addressing import addressees
from .config import AgentChatError, Config
from .matrix import AuthError, Client

# Every lookup of one batch shares this many seconds.
BUDGET_SECONDS = 10.0


@dataclass(frozen=True)
class Thread:
    """One thread as a lookup saw it.

    Attributes:
        root_id: The root's event ID.
        root: The root event, or None when the thread could not be read.
        events: The thread's newest events, oldest first, in the server's order.
        agents: The agent accounts among the root's sender, the agents the root
            mentions and the senders of ``events``.
        posted: The accounts among the root's sender and the senders of
            ``events``.
    """

    root_id: str
    root: dict[str, Any] | None = None
    events: tuple[dict[str, Any], ...] = ()
    agents: frozenset[str] = frozenset()
    posted: frozenset[str] = frozenset()

    @property
    def read(self) -> bool:
        """Tell whether the lookup succeeded."""
        return self.root is not None

    def wakes(self, me: str) -> bool:
        """Tell whether the user's unaddressed message in this thread wakes ``me``.

        It wakes the thread's agents; with no agent seen, or a thread that
        could not be read, it wakes every listener (the rule before threads).
        """
        return not self.read or not self.agents or me in self.agents


def observe(
    root_id: str, root: dict[str, Any], newest_first: list[dict[str, Any]], cfg: Config
) -> Thread:
    """Build the :class:`Thread` a lookup's answers describe."""
    events = tuple(reversed(newest_first))
    posted = {e.get("sender") for e in events} | {root.get("sender")}
    content = root.get("content")
    mentioned = (
        addressees(content, cfg.server_name) if isinstance(content, dict) else set()
    )
    seen = {s for s in posted if isinstance(s, str)}
    return Thread(
        root_id,
        root,
        events,
        frozenset((seen | mentioned) & set(cfg.agents)),
        frozenset(seen),
    )


class Budget:
    """The thread lookups of one sync batch.

    Args:
        client: The listening account's homeserver client.
        cfg: The host's configuration.
        seconds: The time every lookup of the batch shares; it runs on the
            client's clock.
    """

    def __init__(
        self, client: Client, cfg: Config, seconds: float | None = None
    ) -> None:
        self.client = client
        self.cfg = cfg
        spend = BUDGET_SECONDS if seconds is None else seconds
        self.deadline = client.now() + spend
        self._seen: dict[tuple[str, str], Thread] = {}

    def thread(self, room: str, root: str) -> Thread:
        """Return ``root``'s thread in ``room``, asking the server once per batch.

        Raises:
            AuthError: When the token is refused.
        """
        key = (room, root)
        if key not in self._seen:
            try:
                event, chunk = self.client.thread(room, root, self.deadline)
            except AuthError:
                raise
            except AgentChatError:
                self._seen[key] = Thread(root)
            else:
                self._seen[key] = observe(root, event, chunk, self.cfg)
        return self._seen[key]
