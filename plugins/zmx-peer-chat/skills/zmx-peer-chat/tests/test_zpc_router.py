"""The router: who this side is, who the peer is, and when a send refuses.

A send to Codex queues by the thread UUID from the peer's labels, and only
while the Codex zmx session lives and its TUI footer names the bound thread;
otherwise nothing is queued. Peers are found by pair id and role; zero or
several, or another protocol version, refuse. Inside Codex, commands carry
``CODEX_THREAD_ID`` and the daemon's stale ``ZMX_SESSION``, so the thread id
decides who this side is.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from zpc_fakes import PAIR, THREAD_A, THREAD_B, FakeZmx, labels

from zpc.common import ZpcError
from zpc.router import clean_text, find_me, send, tui_shows
from zpc.zmx import Session, parse_ls

FOOTER = "\n› Ask Codex to do anything\n\n  model medium · ~/work · zpc-c0dec0de\n  ? for shortcuts\n"


def _pair(codex_screen: str = FOOTER, **codex_extra: str) -> FakeZmx:
    claude = Session("w-claude", 1, labels("claude", "c1a0de00"))
    codex = Session("w-codex", 2, labels("codex", "c0dec0de", **codex_extra))
    return FakeZmx([claude, codex], {"w-codex": codex_screen})


class Queue:
    """Records what a send would hand to ``codex queue``."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def __call__(self, thread: str, message: str) -> None:
        self.calls.append((thread, message))


@pytest.fixture(autouse=True)
def _no_codex_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    monkeypatch.delenv("ZMX_SESSION", raising=False)


def test_send_to_codex_queues_by_uuid(tmp_path: Path) -> None:
    q = Queue()
    out = send("codex", "hello\n", "w-claude", _pair(thread=THREAD_A), tmp_path, q)
    assert out == "queued"
    assert q.calls == [(THREAD_A, "Chat from Claude: hello")]


def test_dead_codex_session_queues_nothing(tmp_path: Path) -> None:
    zmx = _pair(thread=THREAD_A)
    del zmx.live["w-codex"]
    q = Queue()
    with pytest.raises(ZpcError, match="nothing was sent") as err:
        send("codex", "hello", "w-claude", zmx, tmp_path, q)
    assert err.value.code == 1 and q.calls == []


@pytest.mark.parametrize(
    "screen",
    [
        "\n  model medium · ~/work\n  ? for shortcuts\n",  # after /new: no name
        "\n  model medium · ~/work · zpc-0ther000\n",  # after /resume elsewhere
        FOOTER + "\n".join(f"line {i}" for i in range(10)),  # a dialog covers it
    ],
)
def test_a_tui_that_shows_another_thread_queues_nothing(
    tmp_path: Path, screen: str
) -> None:
    q = Queue()
    with pytest.raises(ZpcError, match="nothing was queued"):
        send("codex", "hi", "w-claude", _pair(screen, thread=THREAD_A), tmp_path, q)
    assert q.calls == []


def test_unbound_codex_session_queues_nothing(tmp_path: Path) -> None:
    q = Queue()
    with pytest.raises(ZpcError, match="no bound Codex thread"):
        send("codex", "hi", "w-claude", _pair(), tmp_path, q)
    assert q.calls == []


def test_several_peers_refuse(tmp_path: Path) -> None:
    zmx = _pair(thread=THREAD_A)
    zmx.live["w-codex2"] = Session("w-codex2", 3, labels("codex", "c0dec0d2"))
    q = Queue()
    with pytest.raises(ZpcError, match="refusing to pick one"):
        send("codex", "hi", "w-claude", zmx, tmp_path, q)
    assert q.calls == []


def test_another_pair_is_no_peer(tmp_path: Path) -> None:
    zmx = _pair(thread=THREAD_A)
    zmx.live["w-codex"].labels["zpc.pair"] = "dsomeotherpair00"
    with pytest.raises(ZpcError, match="no codex session is paired"):
        send("codex", "hi", "w-claude", zmx, tmp_path, Queue())


def test_peer_protocol_mismatch_refuses(tmp_path: Path) -> None:
    zmx = _pair(thread=THREAD_A)
    zmx.live["w-codex"].labels["zpc.proto"] = "2"
    q = Queue()
    with pytest.raises(ZpcError, match="speaks protocol '2'"):
        send("codex", "hi", "w-claude", zmx, tmp_path, q)
    assert q.calls == []


def test_own_protocol_mismatch_refuses(tmp_path: Path) -> None:
    zmx = _pair(thread=THREAD_A)
    zmx.live["w-claude"].labels["zpc.proto"] = "0"
    with pytest.raises(ZpcError, match="speaks protocol '0'"):
        send("codex", "hi", "w-claude", zmx, tmp_path, Queue())


def test_unregistered_session_refuses(tmp_path: Path) -> None:
    zmx = _pair(thread=THREAD_A)
    zmx.live["w-claude"].labels.clear()
    with pytest.raises(ZpcError, match="not registered"):
        send("codex", "hi", "w-claude", zmx, tmp_path, Queue())


def test_cannot_send_to_own_role(tmp_path: Path) -> None:
    with pytest.raises(ZpcError) as err:
        send("claude", "hi", "w-claude", _pair(thread=THREAD_A), tmp_path, Queue())
    assert err.value.code == 2


def test_codex_thread_id_decides_who_this_side_is(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zmx = _pair(thread=THREAD_A)
    monkeypatch.setenv("ZMX_SESSION", "w-claude")  # the daemon's, stale
    monkeypatch.setenv("CODEX_THREAD_ID", THREAD_A)
    assert find_me(zmx.sessions(), None).name == "w-codex"


def test_unbound_codex_thread_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    zmx = _pair(thread=THREAD_A)
    monkeypatch.setenv("ZMX_SESSION", "w-codex")
    monkeypatch.setenv("CODEX_THREAD_ID", THREAD_B)  # after /new
    with pytest.raises(ZpcError, match="no zmx session is bound"):
        find_me(zmx.sessions(), None)
    monkeypatch.setenv("CODEX_THREAD_ID", "not-a-uuid")
    with pytest.raises(ZpcError) as err:
        find_me(zmx.sessions(), None)
    assert err.value.code == 2


def test_zmx_session_names_this_side_outside_codex(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zmx = _pair(thread=THREAD_A)
    with pytest.raises(ZpcError) as err:
        find_me(zmx.sessions(), None)
    assert err.value.code == 2
    monkeypatch.setenv("ZMX_SESSION", "w-claude")
    assert find_me(zmx.sessions(), None).name == "w-claude"
    assert find_me(zmx.sessions(), "w-codex").name == "w-codex"


def test_clean_text_drops_a_self_written_label() -> None:
    label = "Chat from Claude: "
    assert clean_text("  Chat from Claude: Chat from Claude: hi \n", label) == "hi"
    with pytest.raises(ZpcError) as err:
        clean_text(" Chat from Claude: \n", label)
    assert err.value.code == 2


def test_tui_shows_reads_only_the_footer() -> None:
    assert tui_shows(FOOTER, "zpc-c0dec0de")
    assert not tui_shows(FOOTER, "zpc-c0dec0d")
    assert not tui_shows("· zpc-c0dec0de\n" + "x\n" * 10, "zpc-c0dec0de")


def test_parse_ls_reads_labels() -> None:
    text = (
        f"  name=w-codex\tpid=12\tclients=0\tcreated=1\tcwd=file:///w\t"
        f"zpc.pair={PAIR}\tzpc.role=codex\tcmd=codex resume --last\n"
        "→ name=w-shell\tpid=13\tclients=1\tcmd=bash\n"
    )
    got = parse_ls(text)
    assert got["w-codex"].pid == 12
    assert got["w-codex"].labels == {"zpc.pair": PAIR, "zpc.role": "codex"}
    assert got["w-shell"].labels == {}
    with pytest.raises(ZpcError):
        parse_ls("garbage\n")
