"""Shared font-selection and size-mapping helpers for file conversion."""

from __future__ import annotations

import re


DEFAULT_SIZE_MAPPING: dict[float, float] = {16.0: 12.0, 18.0: 14.0, 20.0: 16.0}
DEFAULT_SIZE_MAPPING_TEXT = "16:12, 18:14, 20:16"


def normalize_font_name(name: str | None) -> str:
    """Normalize document/PDF font names for tolerant family matching."""
    if not name:
        return ""
    # Embedded PDF fonts commonly use a six-letter subset prefix.
    value = name.split("+", 1)[-1].casefold()
    value = re.sub(r"(?:regular|normal|book|roman|bold|italic|oblique)$", "", value)
    return re.sub(r"[^a-z0-9]", "", value)


def font_names_match(actual: str | None, selected: str | None) -> bool:
    """Return True when a document font matches the selected source family."""
    wanted = normalize_font_name(selected)
    if not wanted:
        return True
    found = normalize_font_name(actual)
    return bool(found) and (found == wanted or found in wanted or wanted in found)


def parse_size_mapping(value: str) -> dict[float, float]:
    """Parse mappings such as ``16:12, 18->14, 20=16``."""
    mapping: dict[float, float] = {}
    for item in re.split(r"[,;\n]+", value.strip()):
        if not item.strip():
            continue
        match = re.fullmatch(
            r"\s*(\d+(?:\.\d+)?)\s*(?::|=|->)\s*(\d+(?:\.\d+)?)\s*",
            item,
        )
        if not match:
            raise ValueError(
                f"Invalid size mapping {item!r}. Use a format like 16:12, 18:14, 20:16."
            )
        source, target = (float(number) for number in match.groups())
        if source <= 0 or target <= 0:
            raise ValueError("Font sizes must be greater than zero.")
        mapping[source] = target
    return mapping


def mapped_font_size(size: float, mapping: dict[float, float]) -> float:
    """Map a font size, tolerating small floating-point differences in PDFs."""
    for source, target in mapping.items():
        if abs(size - source) <= 0.25:
            return target
    return size
