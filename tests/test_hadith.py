import unittest

from hadith_muaalem.catalog import get_hadith, load_collection
from hadith_muaalem.comparison import compare_texts, tokenize
from hadith_muaalem.gradio_app import select_reference, render_result, reset_reference


class HadithTests(unittest.TestCase):
    def test_collection(self):
        collection = load_collection()
        self.assertEqual([item["number"] for item in collection], list(range(1, 43)))
        self.assertTrue(all(tokenize(item["text"]) for item in collection))
        self.assertIn("الأعمال", tokenize(get_hadith(1)))
        collection[0]["text"] = "changed"
        self.assertNotEqual(get_hadith(1), "changed")
        with self.assertRaises(ValueError):
            get_hadith(43)

    def test_marks_and_punctuation(self):
        self.assertEqual(compare_texts("إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ،", "إنما الأعمال بالنيات")["errors"], [])
        self.assertNotEqual(tokenize("رحمة"), tokenize("رحمه"))
        self.assertNotEqual(tokenize("على"), tokenize("علي"))

    def test_omission_addition_substitution(self):
        for actual, kind in [("إنما بالنيات", "delete"),
                             ("إنما كل الأعمال بالنيات", "insert"),
                             ("إنما الأقوال بالنيات", "replace")]:
            with self.subTest(kind=kind):
                result = compare_texts("إنما الأعمال بالنيات", actual)
                self.assertEqual(len(result["errors"]), 1)
                self.assertEqual(result["errors"][0]["type"], kind)
                self.assertAlmostEqual(result["word_error_rate"], 1 / 3)

    def test_empty_audio_transcript_does_not_pass(self):
        result = compare_texts("إنما الأعمال بالنيات", "")
        self.assertEqual(len(result["errors"]), 3)
        self.assertEqual(result["word_error_rate"], 1)
        with self.assertRaises(ValueError):
            compare_texts("َ،", "كلام")

    def test_repeated_words_and_error_rate_over_one(self):
        result = compare_texts("الله الله", "الله")
        self.assertEqual(len(result["errors"]), 1)
        self.assertGreater(compare_texts("كلمة", "أ ب ج")["word_error_rate"], 1)

    def test_reference_range(self):
        self.assertEqual(select_reference(1, 1, 2), " ".join(get_hadith(1).split()[:2]))
        self.assertEqual(select_reference(1, 1, 0), get_hadith(1))
        self.assertEqual(select_reference(1, None, None), get_hadith(1))
        with self.assertRaises(ValueError):
            select_reference(1, 0, 2)

    def test_html_escaping(self):
        result = {"errors": [dict(type="insert", reference_index=0,
                                 expected="", predicted="<script>alert(1)</script>")]}
        self.assertNotIn("<script>", render_result(result))

    def test_matn_for_all_hadiths(self):
        for number in range(1, 43):
            with self.subTest(number=number):
                matn = get_hadith(number, "matn")
                self.assertTrue(tokenize(matn))
                self.assertLess(len(matn), len(get_hadith(number, "full")))
                self.assertNotIn("رواه", tokenize(matn))
                self.assertNotIn("br", tokenize(matn))

    def test_known_matn_boundaries(self):
        self.assertEqual(" ".join(tokenize(get_hadith(32, "matn"))), "لا ضرر ولا ضرار")
        self.assertEqual(tokenize(get_hadith(1, "matn"))[:3], ["إنما", "الأعمال", "بالنيات"])
        self.assertEqual(tokenize(get_hadith(2, "matn"))[:3], ["بينما", "نحن", "جلوس"])
        self.assertNotIn("وكان", tokenize(get_hadith(40, "matn")))
        self.assertNotIn("السجدة", tokenize(get_hadith(29, "matn")))
        self.assertIn("ألسنتهم", tokenize(get_hadith(29, "matn")))
        self.assertNotIn("وابصة", tokenize(get_hadith(27, "matn")))
        self.assertIn("وابصة", tokenize(get_hadith(27, "full")))

    def test_scope_selection_and_reset(self):
        matn = get_hadith(1, "matn")
        self.assertEqual(select_reference(1, 1, 0, "matn"), matn)
        self.assertEqual(select_reference(1, 1, 2, "matn"), " ".join(matn.split()[:2]))
        self.assertEqual(reset_reference("32", "matn"), (1, 0, get_hadith(32, "matn"), "", "", None))
        with self.assertRaises(ValueError):
            get_hadith(1, "unknown")


if __name__ == "__main__":
    unittest.main()
