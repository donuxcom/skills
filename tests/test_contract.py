import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repo_tool", ROOT / "scripts" / "repo_tool.py")
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


class ContractTests(unittest.TestCase):
    def test_repository_and_skill_contracts(self):
        self.assertEqual([], tool.validate())

    def test_frontmatter_schema_and_collection_version(self):
        for skill in tool.skill_dirs():
            meta, body = tool.parse_frontmatter(skill / "SKILL.md")
            self.assertEqual(skill.name, meta["name"])
            self.assertEqual("Apache-2.0", meta["license"])
            self.assertEqual(tool.VERSION, meta["metadata"]["version"])
            self.assertTrue(all(isinstance(k, str) and isinstance(v, str) for k, v in meta["metadata"].items()))
            self.assertTrue(body.strip())
        provenance = (ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
        self.assertIn(f"- Collection version: {tool.VERSION}", provenance)

    def test_relative_references_resolve(self):
        for skill in tool.skill_dirs():
            self.assertFalse([e for e in tool.validate_skill(skill) if "link" in e])

    def test_catalog_is_fresh_and_complete(self):
        expected = tool.catalog_text()
        self.assertEqual(expected, (ROOT / "catalog.json").read_text(encoding="utf-8"))
        data = json.loads(expected)
        self.assertEqual(tool.VERSION, data["collection_version"])
        self.assertEqual([p.name for p in tool.skill_dirs()], [s["name"] for s in data["skills"]])
        for skill in data["skills"]:
            self.assertEqual("html", skill["default_output_format"])
            self.assertEqual(["html", "markdown"], skill["output_formats"])

    def test_output_format_defaults_and_markdown_option(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for skill in tool.skill_dirs():
            stem = skill.name.removeprefix("dx-")
            skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
            readme_text = (skill / "README.md").read_text(encoding="utf-8")
            for text in (skill_text, readme_text, root_readme):
                self.assertIn(f"`{stem}.html`", text)
                self.assertIn(f"`{stem}.md`", text)
            self.assertIn("--format markdown", skill_text)
            self.assertIn("html` (default)", skill_text)

    def test_missing_prerequisite_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing-skill"
            self.assertTrue(tool.validate_skill(missing))

    def test_existing_output_requires_explicit_overwrite_approval(self):
        for skill in tool.skill_dirs():
            text = (skill / "SKILL.md").read_text(encoding="utf-8").lower()
            self.assertIn("exists", text)
            self.assertIn("explicit approval", text)
            self.assertIn("do not modify it", text)

    def test_prompt_injection_is_untrusted_data(self):
        for skill in tool.skill_dirs():
            text = (skill / "SKILL.md").read_text(encoding="utf-8").lower()
            self.assertIn("prompt injection", text)
            self.assertIn("untrusted data", text)
            self.assertIn("never as instructions", text)


if __name__ == "__main__":
    unittest.main()
