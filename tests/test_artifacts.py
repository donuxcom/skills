import hashlib
import importlib.util
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repo_tool", ROOT / "scripts" / "repo_tool.py")
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


class ArtifactTests(unittest.TestCase):
    def test_build_is_deterministic_and_verifies(self):
        first = tool.build()
        digests_a = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first}
        second = tool.build()
        digests_b = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in second}
        self.assertEqual(digests_a, digests_b)
        self.assertEqual([], tool.verify())

    def test_archive_allowlist_and_modes(self):
        tool.build()
        for archive in sorted((ROOT / "dist").glob("*.zip")):
            skill = archive.name[: -len(f"-{tool.VERSION}.zip")]
            expected = {
                f"{skill}/SKILL.md", f"{skill}/README.md",
                f"{skill}/templates/report-shell.html", "LICENSE",
                "PROVENANCE.md", "THIRD_PARTY_NOTICES.md",
            }
            with zipfile.ZipFile(archive) as zf:
                self.assertEqual(expected, set(zf.namelist()))
                provenance = zf.read("PROVENANCE.md").decode("utf-8")
                self.assertIn(f"- Collection version: {tool.VERSION}", provenance)
                for info in zf.infolist():
                    self.assertEqual(0o100000, (info.external_attr >> 16) & 0o170000)
                    self.assertEqual((1980, 1, 1, 0, 0, 0), info.date_time)


if __name__ == "__main__":
    unittest.main()
