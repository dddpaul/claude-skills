"""agent-chat: agents on different hosts talk through a project's Matrix room.

``send`` posts into the room, ``hook-wait`` waits for a message addressed to
this host's account and hands it to Claude, ``status`` shows what is set up.
The sync loop in :mod:`agent_chat.listen` is shared with the Codex watcher.
"""
