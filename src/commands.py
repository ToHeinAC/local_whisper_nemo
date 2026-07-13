"""Turn a transcript into an ordered plan of text + special-key actions.

Whisper only produces plain text, so spoken formatting words like "new line"
arrive as literal words. This module recognises a small fixed set of them and
splits the transcript into actions the injector can execute:

    parse("intro new line body") ->
        [("text", "intro"), ("key", "enter"), ("text", "body")]

The command match deliberately eats surrounding whitespace and light
punctuation, because Whisper tends to punctuate the spoken command
("... intro. New line, body ...") and we don't want that stray punctuation
landing in the output. The tradeoff: punctuation you genuinely dictated right
next to a command word may be swallowed. The command set is fixed and small,
so there is no config for it.
"""

from __future__ import annotations

import re

_ENTER = ("key", "enter")
_TAB = ("key", "tab")

# More specific phrases first; \b keeps "tab" from matching inside "table".
_COMMAND_RE = re.compile(
    r"[\s.,!?;:]*\b(new\s+paragraph|(?:new|next)\s+line|tab)\b[\s.,!?;:]*",
    re.IGNORECASE,
)


def _actions_for(phrase: str) -> list[tuple[str, str]]:
    normalized = re.sub(r"\s+", " ", phrase.strip().lower())
    if normalized == "new paragraph":
        return [_ENTER, _ENTER]
    if normalized in ("new line", "next line"):
        return [_ENTER]
    return [_TAB]  # only remaining match is "tab"


def parse(text: str) -> list[tuple[str, str]]:
    """Split `text` into ('text', str) and ('key', name) actions in order."""
    actions: list[tuple[str, str]] = []
    pos = 0
    for match in _COMMAND_RE.finditer(text):
        before = text[pos:match.start()].strip()
        if before:
            actions.append(("text", before))
        actions.extend(_actions_for(match.group(1)))
        pos = match.end()
    tail = text[pos:].strip()
    if tail:
        actions.append(("text", tail))
    return actions
