"""Regression tests for Pa-O ASCII-to-Unicode ordering."""

import unittest

from core.engine import convert_pao_ascii_to_unicode


class TestMedialOrdering(unittest.TestCase):
    def test_adjacent_prefix_vowel_syllables(self) -> None:
        for source, expected in (
            ("aAG", "ဗွေ"),
            ("aAGaAG", "ဗွေဗွေ"),
            ("acGacG", "ခွေခွေ"),
            ("aAGaAGaAG", "ဗွေဗွေဗွေ"),
        ):
            with self.subTest(source=source):
                self.assertEqual(convert_pao_ascii_to_unicode(source), expected)

    def test_ra_is_ordered_before_wa_for_every_consonant(self) -> None:
        self.assertEqual(convert_pao_ascii_to_unicode("jzGD;"), "ဖြွီး")

    def test_ya_is_ordered_before_wa_for_every_consonant(self) -> None:
        self.assertEqual(convert_pao_ascii_to_unicode("uGsD;"), "ကျွီး")
