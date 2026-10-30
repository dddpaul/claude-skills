"""The single-flight lock of a wait, with its owner's pid recorded next to it."""

from __future__ import annotations

import fcntl
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import IO


class WaitLock:
    """One wait per (account, room): ``<slug>.lock`` plus ``<slug>.owner``."""

    def __init__(self, state: Path, slug: str) -> None:
        self.path = state / f"{slug}.lock"
        self.owner_file = state / f"{slug}.owner"
        self._f: IO[str] | None = None

    def try_acquire(self) -> bool:
        """Take the lock without blocking; return whether it was taken."""
        f = open(self.path, "a", encoding="utf-8")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            f.close()
            return False
        self._f = f
        return True

    def acquire_within(
        self,
        seconds: float,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.monotonic,
    ) -> bool:
        """Retry the lock for up to ``seconds``; return whether it was taken."""
        end = now() + seconds
        while not self.try_acquire():
            if now() >= end:
                return False
            sleep(0.2)
        return True

    def holder(self) -> int | None:
        """Return the owner pid the current holder recorded, if any."""
        try:
            return int(self.owner_file.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    def record(self, owner: int) -> None:
        """Record ``owner`` as the pid whose Claude this wait serves."""
        tmp = self.owner_file.with_name(f".{self.owner_file.name}.{os.getpid()}")
        tmp.write_text(f"{owner}\n", encoding="utf-8")
        os.replace(tmp, self.owner_file)

    def held(self) -> bool:
        """Tell whether some wait holds the lock (without keeping it)."""
        if self._f is not None:
            return True
        if self.try_acquire():
            self.release()
            return False
        return True

    def release(self) -> None:
        """Remove the owner record, then release the lock, if this object holds it."""
        if self._f is not None:
            try:
                self.owner_file.unlink()
            except FileNotFoundError:
                pass
            self._f.close()
            self._f = None
