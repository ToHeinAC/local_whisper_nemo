"""Clean a raw transcript before it is split into an action plan.

The ASR transcribes faithfully, including two things nobody wants typed:
hesitation sounds ("äh", "uh") and numbers spelled out as words. Both are fixed
here, in this order — dropping the hesitations first lets `alpha2digit` see
"drei äh und zwanzig" as the number it is.

Command words are *not* handled here; `commands.py` runs afterwards on the
cleaned text.
"""

from __future__ import annotations

import re

from text_to_num import alpha2digit

# Only sounds that are never a word in either language. Deliberately excluded:
# "um" (German preposition, and the ", um ... zu" clause is comma-delimited just
# like the English filler, so no rule separates them) and "mhm" (an affirmation).
_HESITATION_RE = re.compile(
    r"[\s,]*\b(?:ähm+|äh+|ähem|öhm*|hm+|uhm+|uh+|erm|umm+)\b[\s,]*",
    re.IGNORECASE,
)

# Isolated numbers are only converted above this threshold, which is how the
# German article survives: "ein Haus" stays a house instead of becoming "1 Haus"
# (likewise English "one house"). Everything from two upwards is converted, as
# are grouped numbers, ordinals ("der dritte" -> "der 3.") and decimals
# ("drei Komma fünf" -> "3,5") regardless of size.
_ISOLATED_NUMBER_THRESHOLD = 1.5


def _languages(locale: str) -> tuple[str, ...]:
    """Map the ASR_LANGUAGE setting to the number-conversion passes to run.

    A pass only ever fires on its own language's number words — running the
    German pass over English text (and vice versa) provably changes nothing —
    so "auto" can simply run both.
    """
    code = locale.strip().lower()[:2]
    return (code,) if code in ("de", "en") else ("de", "en")


def normalize(text: str, locale: str) -> str:
    """Strip hesitation sounds and write spelled-out numbers as digits."""
    cleaned = _HESITATION_RE.sub(" ", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    # A removed leading filler ("Ähm, das ...") would leave the sentence
    # lowercase; restore the capital the speaker clearly intended.
    if cleaned and text[:1].isupper():
        cleaned = cleaned[0].upper() + cleaned[1:]

    for lang in _languages(locale):
        cleaned = alpha2digit(cleaned, lang, _ISOLATED_NUMBER_THRESHOLD)
    return cleaned
