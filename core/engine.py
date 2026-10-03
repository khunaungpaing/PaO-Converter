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
    ASCII_SUBJOINED,
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
    """Replace ASCII '0' with ဝ (wa, U+101D) or leave as ၀ (zero) by context.

    In WinPaOh/Win ASCII keyboards, key '0' is used to type the consonant ဝ (wa).
    Only when '0' is adjacent to other digits (1-9, Myanmar/Pa-O digits) or part
    of a number/decimal/time/date should it remain digit 0 (and later convert to ၀).
    Standalone '0' (or '0' in text/words) represents ဝ.
    """
    non_zero_digits = r"[1-9၁-၉\U000116D1-\U000116D9]"
    num_delims = r"[\.,:/]"

    def replace_zeros(match: re.Match) -> str:
        start = match.start()
        end = match.end()
        prefix = text[max(0, start - 3):start]
        suffix = text[end:min(len(text), end + 3)]

        if re.search(rf"(?:{non_zero_digits}|[0-9၀-၉]{num_delims})$", prefix):
            return match.group(0)
        if re.match(rf"^(?:{non_zero_digits}|{num_delims}[0-9၀-၉])", suffix):
            return match.group(0)

        return "ဝ" * len(match.group(0))

    return re.sub(r"0+", replace_zeros, text)


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
    sub = ASCII_SUBJOINED
    md = ASCII_MEDIALS

    # Reorder each source sequence once. Sequential substitutions can match
    # an already-moved prefix against the next syllable's consonant.
    text = re.sub(
        rf"([{pv}])([{pv}]?)([{fc}])([{sub}]*)([{md}]*)",
        lambda match: match[3] + match[4] + match[2] + match[5] + match[1],
        text,
    )

    # Phase 3: direct mapping
    for key in SORTED_MAP_KEYS:
        text = text.replace(key, ASCII_TO_UNICODE_MAP[key])

    # Phase 4: Unicode ordering post-fixes

    # 1. Vowels & Medials Ordering
    # Myanmar/Pa-O medial order: ျ, ြ, ၞ, ွ, ှ (works after every consonant).
    medial_order = "ျြၞွှ"
    text = re.sub(
        r"[ျြွၞှ]{2,}",
        lambda match: "".join(
            sorted(match.group(), key=medial_order.index)
        ),
        text,
    )

    text = re.sub(r"ေဝ", "ဝေ", text)

    # Move medials before preceding vowels
    # e.g., နိှ (edS) -> နှိ, ညိှ (ndS) -> ညှိ, မိှ (rdS) -> မှိ, ဲွ -> ွဲ
    text = re.sub(
        r"([\u102B-\u1032\u1036]+)([ျြွၞှ]+)",
        r"\2\1",
        text,
    )

    # Sort medials again in case moving vowels made medials adjacent
    text = re.sub(
        r"[ျြွၞှ]{2,}",
        lambda match: "".join(
            sorted(match.group(), key=medial_order.index)
        ),
        text,
    )

    # Subjoined Consonants (ပါဌ်ဆင့်) Ordering
    # Move subjoined consonants before preceding medials, vowels, and diacritics
    # e.g., မိ္မ ("rd®u -> ဓမ္မိက, rd® -> မ္မိ), နြ္ဒေ (ajE´ -> န္ဒြေ)
    text = re.sub(
        r"([\u103B-\u103E\u105E\u102B-\u1032\u1036-\u1038\u108A\u108B]+)(္[\u1000-\u1021](?:[\u103B-\u103E\u105E])*)",
        r"\2\1",
        text,
    )

    # 2. Kinzi (င်္) Ordering
    # Move Kinzi before preceding consonant and its medials
    # e.g., ချင်္ိ (ocsØ) -> င်္ချိ (သင်္ချိုင်း), ကြင်္ (oMuF) -> င်္ကြ (သင်္ကြန်), ဂြင်္ိ (odN+Ø) -> င်္ဂြိ (သိင်္ဂြိုဟ်)
    text = re.sub(
        r"([\u1000-\u102A])([ျြွၞှ]*)([\u102B-\u1032\u1036]*)င်္",
        r"င်္\1\2\3",
        text,
    )

    # 3. Upper/Lower Diacritics Ordering
    text = re.sub(r"\u102F\u102D", "\u102D\u102F", text)  # ု + ိ  -> ိ + ု
    text = re.sub(r"\u1030\u102D", "\u102D\u1030", text)  # ူ + ိ  -> ိ + ူ
    text = re.sub(r"\u1036\u1030", "\u1030\u1036", text)  # ံ + ူ  -> ူ + ံ
    text = re.sub(r"\u1037([\u102D\u102E\u102F\u1030])", r"\1\u1037", text)

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
