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

    def test_la_pan_medial_ordering(self) -> None:
        for source, expected in (
            ("auCmif.", "ကၞောင်ႋ"),
            ("auCmif;", "ကၞောင်း"),
            ("au`mif.", "ကၞောင်ႋ"),
            ("auC~mif.", "ကၞှောင်ႋ"),
            ("au_mif.", "ကၞှောင်ႋ"),
        ):
            with self.subTest(source=source):
                self.assertEqual(convert_pao_ascii_to_unicode(source), expected)

    def test_la_pan_and_ha_hto_medial_ordering(self) -> None:
        """La-pan (ၞ) must precede Ha-hto (ှ) regardless of typing order."""
        for source, expected in (
            ("y`~J", "ပၞှဲ"),
            ("y~`J", "ပၞှဲ"),
            ("yC~J", "ပၞှဲ"),
            ("y~CJ", "ပၞှဲ"),
            ("y_J", "ပၞှဲ"),
            ("y`SJ", "ပၞှဲ"),
            ("yS`J", "ပၞှဲ"),
            ("yCSJ", "ပၞှဲ"),
            ("ySCJ", "ပၞှဲ"),
        ):
            with self.subTest(source=source):
                self.assertEqual(convert_pao_ascii_to_unicode(source), expected)

    def test_vowel_and_medial_ordering(self) -> None:
        """Medials must precede vowels/diacritics regardless of typing order."""
        for source, expected in (
            ("edS", "နှိ"),
            ("ed~", "နှိ"),
            ("ndS", "ညှိ"),
            ("nd~", "ညှိ"),
            ("rdS", "မှိ"),
            ("rd~", "မှိ"),
            ("vdS", "လှိ"),
            ("idS", "ငှိ"),
            ("edSyf", "နှိပ်"),
            ("edSwf", "နှိတ်"),
            ("edSif;", "နှိင်း"),
            ("eSif;", "နှင်း"),
            ("eDS", "နှီ"),
            ("nDS", "ညှီ"),
            ("rDS", "မှီ"),
            ("ekS", "နှု"),
            ("nkS", "ညှု"),
            ("rkS", "မှု"),
            ("elS", "နှူ"),
            ("nlS", "ညှူ"),
            ("rlS", "မှူ"),
            ("eHS", "နှံ"),
            ("rHS", "မှံ"),
        ):
            with self.subTest(source=source):
                self.assertEqual(convert_pao_ascii_to_unicode(source), expected)


class TestUVsNyaResolution(unittest.TestCase):
    def test_nya_lay_combinations(self) -> None:
        """Test combinations where ASCII 'O' must resolve to ဉ (Nya-lay)."""
        test_cases = (
            ("Of", "ဉ်"),
            ("Of;", "ဉ်း"),
            ("Of>", "ဉ်ႋ"),
            ("Of<", "ဉ်ႏ"),
            ("Om", "ဉာ"),
            ("Om;", "ဉား"),
            ("Om‡f", "ဉာဏ်"),
            ("OH", "ဉံ"),
            ("Od", "ဉိ"),
            ("Oö", "ဉ္စ"),
            ("yOö", "ပဉ္စ"),
            ("oOÆm", "သဉ္ဇာ"),
            ("Oä", "ဉ္ဆ"),
            ("OÑ", "ဉ္ဈ"),
            ("0dnmOf", "ဝိညာဉ်"),
        )
        for source, expected in test_cases:
            with self.subTest(source=source):
                self.assertEqual(convert_pao_ascii_to_unicode(source), expected)

    def test_u_vowel_combinations(self) -> None:
        """Test cases where ASCII 'O' remains ဥ (independent vowel U)."""
        test_cases = (
            ("OD;", "ဦး"),
            ("Owk", "ဥတု"),
            ("Oyrm", "ဥပမာ"),
        )
        for source, expected in test_cases:
            with self.subTest(source=source):
                self.assertEqual(convert_pao_ascii_to_unicode(source), expected)


class TestQuotesHandling(unittest.TestCase):
    def test_double_and_single_quotes(self) -> None:
        self.assertEqual(convert_pao_ascii_to_unicode("]]Adkvf<wdkuf}}"), "“ဗိုလ်ႏတိုက်”")
        self.assertEqual(convert_pao_ascii_to_unicode("]Adkvf<wdkuf}"), "‘ဗိုလ်ႏတိုက်’")

    def test_literal_legacy_mappings_preserved(self) -> None:
        self.assertEqual(convert_pao_ascii_to_unicode("1“2"), "၁/၂")
        self.assertEqual(convert_pao_ascii_to_unicode("”"), "ဠ")
        self.assertEqual(convert_pao_ascii_to_unicode("v’"), "လ္လ")


class TestZeroVsWaResolution(unittest.TestCase):
    def test_wa_consonant_contexts(self) -> None:
        test_cases = (
            ("0", "ဝ"),
            ("0 ", "ဝ "),
            (" 0 ", " ဝ "),
            ("00", "ဝဝ"),
            ("0if;", "ဝင်း"),
            ("0if", "ဝင်"),
            ("ytdk0f;", "ပအိုဝ်း"),
            ("a0", "ဝေ"),
            ("0dnmOf", "ဝိညာဉ်"),
            ("0wf", "ဝတ်"),
            ("0uf", "ဝက်"),
            ("0rf;", "ဝမ်း"),
            ("0ef", "ဝန်"),
            ("0yf", "ဝပ်"),
            ("0,f", "ဝယ်"),
        )
        for source, expected in test_cases:
            with self.subTest(source=source):
                self.assertEqual(convert_pao_ascii_to_unicode(source), expected)

    def test_zero_digit_numbers(self) -> None:
        test_cases = (
            ("100", "၁၀၀"),
            ("1000", "၁၀၀၀"),
            ("2024", "၂၀၂၄"),
            ("10", "၁၀"),
            ("50", "၅၀"),
            ("09", "၀၉"),
            ("01", "၀၁"),
            ("09-123456", "၀၉-၁၂၃၄၅၆"),
        )
        for source, expected in test_cases:
            with self.subTest(source=source):
                self.assertEqual(convert_pao_ascii_to_unicode(source), expected)


class TestSubjoinedConsonantOrdering(unittest.TestCase):
    def test_subjoined_consonant_after_vowels(self) -> None:
        """In Win ASCII typing, vowels/diacritics typed before subjoined consonants
        must be reordered to canonical Unicode: Base + Virama + Subjoined + Vowels.
        """
        test_cases = (
            ("\"rd®u", "ဓမ္မိက"),
            ("rd®", "မ္မိ"),
            ("r®d", "မ္မိ"),
            ("owdå", "သတ္တိ"),
            ("udú", "က္ကိ"),
            ("pdö", "စ္စိ"),
            ("rD®", "မ္မီ"),
            ("rk®", "မ္မု"),
            ("wdÉ", "တ္တွိ"),
            ("arwåm", "မေတ္တာ"),
        )
        for source, expected in test_cases:
            with self.subTest(source=source):
                self.assertEqual(convert_pao_ascii_to_unicode(source), expected)

