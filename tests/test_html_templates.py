from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class TemplateParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.fragment_links = []
        self.tags = []
        self.attrs = []
        self.csp = None

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        values = dict(attrs)
        self.attrs.extend(attrs)
        element_id = values.get("id")
        href = values.get("href")
        http_equiv = values.get("http-equiv")
        if tag == "meta" and http_equiv is not None and http_equiv.lower() == "content-security-policy":
            self.csp = values.get("content")
        if element_id is not None:
            self.ids.add(element_id)
        if href is not None and href.startswith("#"):
            self.fragment_links.append(href[1:])


class HtmlTemplateTests(unittest.TestCase):
    def templates(self):
        return sorted(SKILLS.glob("*/templates/report-shell.html"))

    def test_every_skill_has_the_same_report_shell(self):
        skills = sorted(path for path in SKILLS.iterdir() if path.is_dir())
        templates = self.templates()
        self.assertEqual(len(skills), len(templates))
        contents = {path.read_text(encoding="utf-8") for path in templates}
        self.assertEqual(1, len(contents), "report shells must stay synchronized")

    def test_report_shell_is_standalone_accessible_and_responsive(self):
        for path in self.templates():
            text = path.read_text(encoding="utf-8")
            lower = text.lower()
            parser = TemplateParser()
            parser.feed(text)
            with self.subTest(path=path):
                self.assertTrue(lower.startswith("<!doctype html>"))
                self.assertIn('<meta name="viewport"', lower)
                self.assertIn("<main", lower)
                self.assertIn("<nav", lower)
                self.assertIn("@media (max-width:", lower)
                self.assertIn("@media print", lower)
                self.assertIn("prefers-reduced-motion", lower)
                self.assertIn(":focus-visible", lower)
                self.assertIn("skip-link", lower)
                self.assertRegex(lower, re.compile(r"\.toc\s*\{[^}]*position:\s*sticky", re.DOTALL))
                self.assertRegex(lower, re.compile(r"\.toc ol\s*\{[^}]*overflow-x:\s*auto", re.DOTALL))
                self.assertIn("scroll-margin-top: 5rem", lower)
                self.assertIn("scroll-padding-top: 5rem", lower)
                self.assertIn("calc(90rem + 2 * var(--gutter))", lower)
                self.assertIn(".grid + .reading", lower)
                self.assertIsNotNone(parser.csp)
                csp = parser.csp or ""
                self.assertIn("default-src 'none'", csp)
                self.assertIn("script-src 'none'", csp)
                self.assertIn("object-src 'none'", csp)
                self.assertIn("form-action 'none'", csp)
                forbidden_tags = {"script", "iframe", "object", "embed", "form", "input", "button", "textarea", "select", "base", "link"}
                self.assertEqual(set(), forbidden_tags & set(parser.tags))
                self.assertFalse(any(name.lower().startswith("on") for name, _ in parser.attrs))
                self.assertFalse(any(name.lower() == "style" for name, _ in parser.attrs))
                for name, value in parser.attrs:
                    if name.lower() in {"href", "src", "action", "formaction"} and value is not None:
                        self.assertFalse(re.match(r"(?i)\s*(?:https?:|javascript:|vbscript:|data:)", value))
                self.assertEqual([], sorted(set(parser.fragment_links) - parser.ids))

    def test_report_shell_has_accessible_tables_and_fallbacks(self):
        for path in self.templates():
            text = path.read_text(encoding="utf-8").lower()
            with self.subTest(path=path):
                self.assertIn("<caption>", text)
                self.assertIn('scope="col"', text)
                self.assertIn("@media (forced-colors: active)", text)
                self.assertIn("table { min-width: 0; }", text)

    def test_report_shell_contains_donux_design_tokens(self):
        required = ("#000000", "#171717", "#454646", "#25c472", "#0072c6", "#b700d4", "#ed5d44")
        for path in self.templates():
            text = path.read_text(encoding="utf-8").lower()
            with self.subTest(path=path):
                for token in required:
                    self.assertIn(token, text)
                self.assertRegex(text, re.compile(r"max-width:\s*var\(--reading\)"))


if __name__ == "__main__":
    unittest.main()
