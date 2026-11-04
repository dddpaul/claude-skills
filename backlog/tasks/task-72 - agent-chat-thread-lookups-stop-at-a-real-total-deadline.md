---
id: TASK-72
title: agent-chat thread lookups stop at a real total deadline
status: Done
assignee: []
created_date: '2026-11-04T14:51:00Z'
updated_date: '2026-11-04T17:27:00Z'
labels:
  - feature:agent-chat-threads
dependencies:
  - TASK-71
priority: low
ordinal: 72000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

A review of the threads feature (agent-chat 0.4.1) found that the 10 s lookup budget is not a total deadline.

- **What the bounded mode does.** `matrix.Client.request(..., tries=2)` is the mode thread lookups use. It caps each
  socket wait at the time that is left: `http.client` gets that as its timeout, and the timeout applies to each socket
  operation, not to the request.
- **How it fails.** A response that drips bytes faster than that timeout keeps `resp.read()` going past the deadline,
  and a success that arrives late is still returned. Reproduced with a local HTTP server that sends one byte every
  20 ms: a request with a 0.15 s budget returned success after 0.95 s.
- **Other ways past the deadline.** Separate waits for connect, the CONNECT tunnel, the TLS handshake, the headers and
  the body add up the same way. The hostname lookup (getaddrinfo) is not bounded at all.
- **Why it matters.** Lookups run before any delivery, so a slow server can hold every room's mail.
- **Why it is P3.** The deployed homeserver and proxy fail by stalling or closing, which the existing stall test
  covers.

## Locked decisions

- **Scope.** Only the bounded mode (`tries` set) changes. Send and sync, the unbounded calls, keep their behaviour.
- **A total deadline.** A bounded request ends by its deadline whatever the server does: it fails with
  `NetworkError`, and a success that completes after the deadline is treated as a failure.
- **A suggested mechanism, not a requirement.**
  - Connect explicitly (`conn.connect()`) with the socket timeout set to the time that is left.
  - Once `conn.sock` exists, including after the CONNECT tunnel and the TLS wrap, arm a `threading.Timer` for the
    time that is left. The timer calls `sock.shutdown(socket.SHUT_RDWR)`, which interrupts a blocked read.
  - Cancel the timer in `finally`.
  - Check the clock after the response is read.

  The socket's ownership must be explicit: the timer must never touch a socket that has been closed or replaced.
- **DNS.** getaddrinfo is not bounded. The README says so; do not claim otherwise.

## Scope cuts

- **No change to unbounded requests.**
- **No async rewrite, no third-party HTTP library.**
- **No DNS bounding.**

## Paths

- The code is `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/matrix.py`.
- The tests are in `plugins/agent-chat/skills/agent-chat/tests/`, in test_agent_chat_transport.py.
- The doc is `plugins/agent-chat/README.md`, in its Threads row: "no socket waits past the budget" becomes a total
  deadline that leaves DNS out.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A test with a local HTTP server that sends its response one byte every 20 ms shows a bounded request with a 0.15 s budget fails with NetworkError within 0.65 s
- [x] #2 Tests show a slow-headers response and a slow-body response both fail within the budget plus 0.5 s, and the existing silent-peer stall test still passes
- [x] #3 A test shows a connect that never completes (a listening socket that never accepts or answers) fails within the budget plus 0.5 s
- [x] #4 A test shows a bounded request whose response completes after its deadline is reported as a failure, not a success
- [x] #5 A test runs 50 bounded requests and shows no watchdog thread is left alive afterwards
- [x] #6 Unbounded requests (send, sync) are unchanged: their existing tests pass unmodified
- [x] #7 The plugin README Threads row says the lookup budget bounds connect, headers and body, and that the hostname lookup is not bounded
- [x] #8 agent-chat version is 0.4.3 in plugins/agent-chat/.claude-plugin/plugin.json, plugins/agent-chat/.codex-plugin/plugin.json and the version pin in test_agent_chat_codex.py
- [x] #9 uv run ruff check . is clean and uv run pytest plugins/agent-chat passes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: _once takes the bounded request's deadline; a _Watchdog (threading.Timer, named, joined on cancel) armed before connect shuts down the connection's socket at the deadline - the live conn.sock while connecting/tunnelling, the pinned socket once connected (so an internal close on Connection: close cannot hide the body's socket). Cancel under a lock before conn.close, so the timer never touches a closed socket. After the read, a fired watchdog or a passed deadline turns the answer into a TimeoutError (a network failure). Tests with a local drip server: drip, slow headers, slow body, never-accepting listener, late success via injected clock, 50 requests leave no watchdog thread. README Threads row, version 0.4.3.

Commit: `95071ec` - task-72: agent-chat bounded requests end by a total deadline through a socket watchdog

Commit: `54b479d` - task-72: agent-chat bounded TLS handshake gets the time left, a watchdog fired while connecting fails the request

Commit: `a6e30c8` - task-72: agent-chat bounded connects share the time left across a host's addresses

Re-review 2 (interactive, after the Ralph run ended mid-review): CHANGES REQUESTED, score 5. Both first-review findings confirmed fixed (connect/tunnel/TLS cases end by the budget; the late-answer test passed 300/300). New blocking B1: socket.create_connection gave every resolved address the full timeout, so N unreachable addresses took N budgets. Fixed: Client._dial() replaces conn._create_connection for bounded requests; each address gets only the time left and the loop stops once it is spent. Regression test: three stalling addresses, 0.3 s budget, ends < 0.8 s and their timeouts sum to the budget (fails on the previous code at 0.95 s). Minors fixed: tls_context() now sets post_handshake_auth like http.client and its docstring says a _create_default_https_context override does not reach it; the _Watchdog docstring says which closed sockets the timer can reach and why that is harmless.

Commit: `1c8aca2` - task-72: agent-chat bounded connect skips an address family the host cannot create

Re-review 3: CHANGES REQUESTED, score 5. The multi-address fix holds directly and through a proxy, unbounded requests still use socket.create_connection, IPv6 and source_address work. New blocking: _dial created the socket outside its try, so an address family the host cannot create (EAFNOSUPPORT, e.g. ::1 first on a host with IPv6 disabled) failed the whole connect instead of falling through, a regression from a6e30c8. Fixed: the socket is created inside the try, as socket.create_connection does. Tests: an AF_INET6 that cannot be created followed by a reachable IPv4 succeeds (fails on the previous code); the multi-address test now also runs through a proxy and checks the proxy's hostname is the one resolved. ruff clean; pytest plugins/agent-chat 202 passed.

Commit: `aa85681` - task-72: agent-chat hands a fresh bounded socket to the watchdog under its lock, so a late connect never reaches the tunnel

Re-review 4: CHANGES REQUESTED, score 5. The review-3 fixes hold; _dial matches socket.create_connection apart from all_errors and the empty-list message (unreachable). New blocking: a connect that returned after the watchdog fired (conn.sock still None, so the fire only set the flag) went on into _tunnel() with the old socket timeout, so a dripping proxy held the request (simulated 3.63 s on a 0.3 s budget). Fixed: _Watchdog.adopt(sock) pins the fresh socket under the watchdog's lock and returns False once it fired; _dial then closes it and raises TimeoutError. Regression test: a connect that succeeds but returns after its timeout, through a proxy that drips its CONNECT answer: 0.35 s now, 2.42 s on the previous code. Full suite 203 passed; the 16 deadline tests raise no ResourceWarning and passed 30 runs of 30; the proxy-host-name test's ResourceWarnings also occur with master's matrix.py.

Commit: `1ff13fd` - task-72: agent-chat watchdog docstring credits adopt for cutting the proxy tunnel

Re-review 5: APPROVED, score 9 (0 blocking, 1 minor). The adopt/_fire/hold/cancel ordering was stress-probed (300 requests with connects within ±30 ms of the watchdog firing): every shutdown hit an adopted socket, no refused socket was ever shut, slowest request 0.15 s, no watchdog thread left. The minor (the _Watchdog docstring still described the pre-adopt mechanism) was fixed afterwards as a docstring-only change, with the conn.sock fallback in _fire labelled a guard. Final: uv run ruff check . clean, ruff format --check clean, uv run pytest plugins/agent-chat 203 passed (outside the sandbox, which blocks local ports). The Ralph run that implemented 95071ec and 54b479d ended mid re-review; reviews 2-5 and their fixes (a6e30c8, 1c8aca2, aa85681) ran interactively.
<!-- SECTION:NOTES:END -->
