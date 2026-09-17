import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((ROOT / "tests" / "fixtures" / "activation_cases.json").read_text(encoding="utf-8"))

    def test_every_skill_has_three_positive_and_three_negative_cases(self):
        expected = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
        self.assertEqual(expected, set(self.cases))
        for name, cases in self.cases.items():
            with self.subTest(skill=name):
                self.assertGreaterEqual(len(cases["positive"]), 3)
                self.assertGreaterEqual(len(cases["negative"]), 3)
                self.assertTrue(all(isinstance(x, str) and x.strip() for x in cases["positive"] + cases["negative"]))
                self.assertFalse(set(cases["positive"]) & set(cases["negative"]))

    def test_activation_descriptions_are_distinct_and_bounded(self):
        descriptions = []
        for name in sorted(self.cases):
            first = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8").splitlines()[2]
            description = first.split(":", 1)[1].strip()
            self.assertIn("Use when", description)
            self.assertTrue("do not use for" in description or "not for" in description)
            self.assertLessEqual(len(description), 1024)
            descriptions.append(description)
        self.assertEqual(len(descriptions), len(set(descriptions)))


if __name__ == "__main__":
    unittest.main()
