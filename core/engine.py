"""
Pa-O ASCII → Unicode conversion engine.

Conversion pipeline:
  Phase 1  – Pre-cleanup swaps
  Phase 1.2 – Resolve '0' as ဝ (wa) or ၀ (zero)
  Phase 1.5 – Quote/bracket substitution
  Phase 2  – Reorder prefix vowels / medials
  Phase 3  – Direct character mapping
  Phase 4  – Unicode ordering post-fixes
  Phase 5  – NFC normalisation
"""

import unicodedata
import regex as re

from .mapping import (
    ASCII_PRE_CLEANUP,
    ASCII_PREFIX_VOWELS,
    ASCII_MEDIALS,
    ASCII_VOWELS_AND_MEDIALS,
    FILTERED_CONSONANTS,
    QUOTES_MAP,
    SORTED_MAP_KEYS,
    SORTED_QUOTE_KEYS,
    ASCII_TO_UNICODE_MAP,
)


def resolve_zero_and_wa(text: str) -> str:
    """Replace ASCII '0' with ဝ (wa, U+101D) or leave as ၀ (zero) by context."""
    text = re.sub(rf"0({ASCII_VOWELS_AND_MEDIALS})", r"ဝ\1", text)
    text = re.sub(rf"({ASCII_VOWELS_AND_MEDIALS})0", r"\1ဝ", text)
    text = re.sub(rf"0([{FILTERED_CONSONANTS}])", r"ဝ\1", text)
    text = re.sub(rf"([{FILTERED_CONSONANTS}])0", r"\1ဝ", text)
    return text


def convert_pao_ascii_to_unicode(text: str) -> str:
    """Convert a Pa-O WinPaOh ASCII string to Myanmar Unicode (Ext-C / Pa-O)."""
    if not text:
        return ""

    # Phase 1: pre-cleanup
    for wrong, right in ASCII_PRE_CLEANUP.items():
        text = text.replace(wrong, right)

    # Phase 1.2: ဝ vs ၀
    text = resolve_zero_and_wa(text)

    # Phase 1.5: quotes
    for key in SORTED_QUOTE_KEYS:
        text = text.replace(key, QUOTES_MAP[key])

    # Phase 2: reorder prefix vowels + medials
    pv = ASCII_PREFIX_VOWELS
    fc = FILTERED_CONSONANTS
    md = ASCII_MEDIALS

    # Reorder each source sequence once. Sequential substitutions can match
    # an already-moved prefix against the next syllable's consonant.
    text = re.sub(
        rf"([{pv}])([{pv}]?)([{fc}])([{md}]*)",
        lambda match: match[3] + match[2] + match[4] + match[1],
        text,
    )

    # Phase 3: direct mapping
    for key in SORTED_MAP_KEYS:
        text = text.replace(key, ASCII_TO_UNICODE_MAP[key])

    # Phase 4: Unicode ordering post-fixes

    # 1. Vowels & Medials Ordering
    # Myanmar medial order: ျ, ြ, ွ, ှ (works after every consonant).
    medial_order = "ျြွှ"
    text = re.sub(
        r"[ျြွှ]{2,}",
        lambda match: "".join(
            sorted(match.group(), key=medial_order.index)
        ),
        text,
    )

    text = re.sub(r"ေဝ", "ဝေ", text)
    text = re.sub(r"ဲွ", "ွဲ", text)
    text = re.sub(r"ဲြ", "ြဲ", text)
    text = re.sub(r"ဲျ", "ျဲ", text)

    # 2. Upper/Lower Diacritics Ordering
    text = re.sub(r"\u1030\u102D", "\u102D\u1030", text)  # ူ + ိ  -> ိ + ူ
    text = re.sub(r"\u1036\u1030", "\u1030\u1036", text)  # ံ + ူ  -> ူ + ံ
    text = re.sub(r"\u1037([\u102D\u102E\u102F\u1030])", r"\1\u1037", text)

    # 3. Kinzi (င်္) Ordering
    text = re.sub(r"([\u1000-\u102A])(\u103E)?င်္", r"င်္\1\2", text)

    # Parentheses post-fix (WinPaOh '…' နဲ့ '•' ကို Unicode ကွင်းစ/ကွင်းပိတ် သို့ အဆုံးမှ ပြောင်းခြင်း)
    text = text.replace("…", "(").replace("•", ")")

    # Phase 5: NFC normalisation
    return unicodedata.normalize("NFC", text)
