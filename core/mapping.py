"""
Pa-O WinPaOh ASCII → Unicode mapping tables and derived character sets.
All data is read-only; nothing here should be mutated at runtime.
"""
LA_PAN: str = "ၞ"
HTUN_PLA: str = "ှ"
KAM_SONG_PHRONE: str = "ႏ"

ASCII_TO_UNICODE_MAP: dict[str, str] = {
    # Pa-O Ext-C & Tone Marks
    "`": LA_PAN,
    "~": HTUN_PLA,
    "<": KAM_SONG_PHRONE,
    ">": "ႋ",

    # Numbers & Symbols
    "1": "၁", "!": "\U000116D1",
    "2": "၂", "@": "\U000116D2",
    "3": "၃", "#": "\U000116D3",
    "4": "၄", "$": "\U000116D4",
    "5": "၅", "%": "\U000116D5",
    "6": "၆", "^": "\U000116D6",
    "7": "၇", "&": "\U000116D7",
    "8": "၈", "*": "\U000116D8",
    "9": "၉", "(": "\U000116D9",
    "0": "၀", ")": "\U000116D0",
    "-": "-", "_": f"{LA_PAN}{HTUN_PLA}",
    "=": "=", "+": "ဂ",

    # First Row
    "q": "ဆ", "Q": "ျှ",
    "w": "တ", "W": "ျွှ",
    "e": "န", "E": "န",
    "r": "မ", "R": "ျွ",
    "t": "အ", "T": "ွှ",
    "y": "ပ", "Y": "့",
    "u": "က", "U": "့",
    "i": "င", "I": "ှု",
    "o": "သ", "O": "ဥ",
    "p": "စ", "P": "ရ",
    "[": "ဟ", "{": "ဧ",
    "]": "\u2018", "}": "\u2018",
    "\\": "၏", "|": "ဋ္ဌ",

    # Home Row
    "a": "ေ", "A": "ဗ",
    "s": "ျ", "S": "ှ",
    "d": "ိ", "D": "ီ",
    "f": "်", "F": "င်္",
    "g": "ါ", "G": "ွ",
    "h": "့", "H": "ံ",
    "j": "ြ", "J": "ဲ",
    "k": "ု", "K": "ု",
    "l": "ူ", "L": "ူ",
    ";": "း", ":": "ါ်",
    "'": "ဒ", '"': "ဓ",

    # Bottom Row
    "z": "ဖ", "Z": "ဇ",
    "x": "ထ", "X": f"{HTUN_PLA}ူ",
    "c": "ခ", "C": LA_PAN,
    "v": "လ", "V": f"{HTUN_PLA}ု",
    "b": "ဘ", "B": "ြ",
    "n": "ည", "N": "ြ",
    "m": "ာ", "M": "ြ",
    ",": "ယ", ".": "ႋ",
    "/": "။", "?": "၊",

    # ပါဌ်ဆင့်များ
    "¢": "္ဃ", "¦": "္ထ",
    "¨": "္ဓ", "©": "္ခ",
    "¬": "္ထ", "®": "္မ",
    "²": "္ဌ", "³": "္ဋ",
    "´": "္ဒ", "¾": "္ဂ",
    "Á": "္ဗ", "Å": "္တ",
    "Æ": "္ဇ", "Ç": "္ဘ",
    "É": "္တွ", "Ñ": "္ဈ",
    "Ö": "္ဏ", "Ü": "္ပ",
    "ä": "္ဆ", "å": "္တ",
    "æ": "္ဖ", "é": "္န",
    "ö": "္စ", "ú": "္က",
    "’": "္လ",

    # အခြားစာလုံးများ
    "£": "ဣ", "¤": "၎",
    "¥": "ဋ္ဋ",  "§": "ှ",
    "È": "ရျ", "Ì": "-",
    "Í": "ဉ", "Ð": "င်္ီ",
    "Ó": "ဉာ", "µ": "ဍ္ဍ",
    "Ø": "င်္ိ", "Ù": "ဌ",
    "Ú": "ဉ", "ß": "ျ",
    "ç": ",", "í": "၍",
    "ð": "ိံ", "ñ": "ည",
    "ø": "င်္ံ", "ü": "၌",
    "þ": "ဤ", "\xA0": "+",
    "Œ": "×", "œ": "÷",
    "–": "ဎ", "—": "ြ",
    "‚": "ြ", "“": "/",
    "”": "ဠ", "„": "ဃ",
    "‡": "ဏ", "‰": "%",
    "‹": "ကျပ်", "›": "ဋ",
    "™": "ဍ", "ó": "ဿ",
    "½": "ရ",
}

UNICODE_CONSONANTS: frozenset[str] = frozenset({
    "က", "ခ", "ဂ", "ဃ", "င", "စ", "ဆ", "ဇ", "ဈ", "ဉ", "ည",
    "ဋ", "ဌ", "ဍ", "ဎ", "ဏ", "တ", "ထ", "ဒ", "ဓ", "န", "ပ",
    "ဖ", "ဗ", "ဘ", "မ", "ယ", "ရ", "လ", "ဝ", "သ", "ဟ", "ဠ", "အ",
})

ASCII_CONSONANTS: str = "".join(
    k for k, v in ASCII_TO_UNICODE_MAP.items() if v in UNICODE_CONSONANTS
)

# ေ (a) and ြ (j, B, N, M) are written before their base consonant in ASCII
ASCII_PREFIX_VOWELS: str = "ajBNM"

# Consonants that can appear adjacent to '0' to identify it as ဝ (wa)
FILTERED_CONSONANTS: str = (
    "".join(c for c in ASCII_CONSONANTS if c not in ASCII_PREFIX_VOWELS) + "0"
)

ASCII_VOWELS_AND_MEDIALS: str = r"[aDd kKlLhHjJGSfYUmg]"

ASCII_MEDIALS: str = "sGSjBNMQWRT~_"

# Quotes resolved before main mapping to avoid double-substitution
QUOTES_MAP: dict[str, str] = {
    "]]": "\u201C",
    "}}": "\u201D",
    "]": "\u2019",
    "}": "\u2019",
}

ASCII_PRE_CLEANUP: dict[str, str] = {
    "d`V": f"{LA_PAN}{HTUN_PLA}dk", "dCV": f"{LA_PAN}{HTUN_PLA}dk",
    "kd": "dk", "Kd": "dK", # ို
    "kD": "Dk", "KD": "DK", # ီု
    "dG": "Gd", # ွိ
    "DG": "GD", # ွီ
    "JG": "GJ", # ွဲ
    "Hk": "kH", "HK": "KH",# ုံ
    "if": "င်",

    "dV": f"{HTUN_PLA}ို", "Vd": f"{HTUN_PLA}ို",
    "DV": f"{HTUN_PLA}ီု", "VD": f"{HTUN_PLA}ီု",
    "dX": f"{HTUN_PLA}ိူ", "Xd": f"{HTUN_PLA}ိူ",
    "DX": f"{HTUN_PLA}ီူ", "XD": f"{HTUN_PLA}ီူ",
    "d~": "~d", "d`": "`d", "D`": "`D",
    "dC": "Cd",

    "dI": "ှို", "Id": "ှို",
    "DI": "ှီု", "ID": "ှီု",
    "J~": "~J", "C~": f"{LA_PAN}{HTUN_PLA}",
    "Of": "ဉ်", "OH": "ဉံ", "Od":"ဉိ", "OD;": "ဦး", "Om": "ဉာ"
}

# Pre-sorted keys (longest first) to avoid partial-match replacement bugs
SORTED_MAP_KEYS: list[str] = sorted(ASCII_TO_UNICODE_MAP, key=len, reverse=True)
SORTED_QUOTE_KEYS: list[str] = sorted(QUOTES_MAP, key=len, reverse=True)
