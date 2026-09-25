"""Register bundled fonts with Qt and return their family names."""

import os

from PyQt6.QtGui import QFontDatabase

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
_ASCII_FONT_FILE = os.path.join(_ASSETS, "kothupaoh1.ttf")
_UNI_FONT_FILE = os.path.join(_ASSETS, "KhamThaton-Exp-Regular-0.2.ttf")


def load_application_fonts() -> tuple[str, str]:
    """
    Register bundled fonts and return (ascii_family, unicode_family).
    Falls back to font-name strings if registration fails.
    """
    ascii_id = QFontDatabase.addApplicationFont(_ASCII_FONT_FILE)
    uni_id = QFontDatabase.addApplicationFont(_UNI_FONT_FILE)

    ascii_family = (
        QFontDatabase.applicationFontFamilies(ascii_id)[0]
        if ascii_id != -1 else "WinPaOh"
    )
    uni_family = (
        QFontDatabase.applicationFontFamilies(uni_id)[0]
        if uni_id != -1 else "KhamThaton"
    )
    return ascii_family, uni_family


def make_unicode_font(family: str, size: int) -> "QFont":
    """Create the Unicode display font."""
    from PyQt6.QtGui import QFont

    return QFont(family, size)
