"""The command line: exit codes and the codex-cli version gate."""

from __future__ import annotations

from pathlib import Path

import pytest
import zpc_fakes  # noqa: F401 - puts the zpc package on sys.path

from zpc.cli import is_tested_codex, main
from zpc.common import TESTED_CODEX_CLI


@pytest.mark.parametrize(
    ("output", "tested"),
    [
        (f"codex-cli {TESTED_CODEX_CLI}", True),
        (f"codex-cli {TESTED_CODEX_CLI}\n", True),
        (f"codex-cli 1{TESTED_CODEX_CLI}", False),
        (f"codex-cli {TESTED_CODEX_CLI}.1", False),
        ("", False),
    ],
)
def test_only_the_tested_codex_version_passes(output: str, tested: bool) -> None:
    assert is_tested_codex(output) is tested


def test_a_refusal_prints_its_reason_and_exit_code(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("ZPC_MAIL_DIR", str(tmp_path / "mail"))
    monkeypatch.delenv("ZMX_SESSION", raising=False)
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    assert main(["prepare-message", "../escape"]) == 2
    assert "zmx-peer-chat: bad message file name" in capsys.readouterr().err
