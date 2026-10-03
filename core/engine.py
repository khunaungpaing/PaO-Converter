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
    ASCII_NYA_FOLLOWERS,
    FILTERED_CONSONANTS,
    QUOTES_MAP,
    SORTED_MAP_KEYS,
    SORTED_QUOTE_KEYS,
    ASCII_TO_UNICODE_MAP,
    PLACEHOLDER_OPEN_DOUBLE,
    PLACEHOLDER_CLOSE_DOUBLE,
    PLACEHOLDER_OPEN_SINGLE,
    PLACEHOLDER_CLOSE_SINGLE,
)


def resolve_zero_and_wa(text: str) -> str:
    """Replace ASCII '0' with ဝ (wa, U+101D) or leave as ၀ (zero) by context."""
    # 1. 0 adjacent to any non-digit Unicode Myanmar character (e.g. င် from pre-cleanup)
    non_digit_myanmar = r"[\u1000-\u103F\u104A\u104B\u104E-\u109F]"
    text = re.sub(rf"0({non_digit_myanmar})", r"ဝ\1", text)
    text = re.sub(rf"({non_digit_myanmar})0", r"\1ဝ", text)

    # 2. 0 adjacent to ASCII vowels, medials, diacritics, and tone marks
    text = re.sub(rf"0({ASCII_VOWELS_AND_MEDIALS})", r"ဝ\1", text)
    text = re.sub(rf"({ASCII_VOWELS_AND_MEDIALS})0", r"\1ဝ", text)

    # 3. 0 adjacent to ASCII consonants
    text = re.sub(rf"0([{re.escape(FILTERED_CONSONANTS)}])", r"ဝ\1", text)
    text = re.sub(rf"([{re.escape(FILTERED_CONSONANTS)}])0", r"\1ဝ", text)

    # 4. Standalone 00 (not surrounded by digits) represents ဝဝ (e.g. ဝဝဖြိုးဖြိုး)
    text = re.sub(r"(?<![0-9၀-၉])00(?![0-9၀-၉])", "ဝဝ", text)

    return text


def resolve_u_and_nya(text: str) -> str:
    """Replace ASCII 'O' with ဉ (nya-lay, U+1009) or leave as ဥ (u, U+1025) by context.

    In WinPaOh/Win ASCII, 'O' represents both ဉ and ဥ:
    - Followed by any subjoined consonant (ပါဌ်ဆင့်), asat 'f' (်), 'm' (ာ),
      'H' (ံ), or 'd' (ိ): ALWAYS ဉ (Nya-lay).
    - Standalone or followed by 'D' (ီ, as in OD; -> ဦး) or normal consonants
      (e.g., Owk -> ဥတု, Oyrm -> ဥပမာ): remains ဥ.
    """
    return re.sub(rf"O([{re.escape(ASCII_NYA_FOLLOWERS)}])", r"ဉ\1", text)


def convert_pao_ascii_to_unicode(text: str) -> str:
    """Convert a Pa-O WinPaOh ASCII string to Myanmar Unicode (Ext-C / Pa-O)."""
    if not text:
        return ""

    # Phase 1: pre-cleanup
    for wrong, right in ASCII_PRE_CLEANUP.items():
        text = text.replace(wrong, right)

    # Phase 1.2: ဝ vs ၀
    text = resolve_zero_and_wa(text)

    # Phase 1.3: ဉ vs ဥ
    text = resolve_u_and_nya(text)

    # Phase 1.5: quotes
    for key in SORTED_QUOTE_KEYS:
        text = text.replace(key, QUOTES_MAP[key])

    # Phase 2: reorder prefix vowels + medials
    pv = ASCII_PREFIX_VOWELS
    fc = FILTERED_CONSONANTS + "ဝ"
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

    # Parentheses and quotes post-fix
    text = text.replace("…", "(").replace("•", ")").replace("ႋႋႋ", "...")
    text = (
        text.replace(PLACEHOLDER_OPEN_DOUBLE, "\u201C")
        .replace(PLACEHOLDER_CLOSE_DOUBLE, "\u201D")
        .replace(PLACEHOLDER_OPEN_SINGLE, "\u2018")
        .replace(PLACEHOLDER_CLOSE_SINGLE, "\u2019")
    )

    # Phase 5: NFC normalisation
    return unicodedata.normalize("NFC", text)
