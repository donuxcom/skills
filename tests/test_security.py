import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repo_tool", ROOT / "scripts" / "repo_tool.py")
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


class SecurityTests(unittest.TestCase):
    def test_public_tree_security_scan(self):
        self.assertEqual([], tool.security_scan())

    def test_sensitive_files_and_excluded_directories_are_not_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "safe.md").write_text("safe", encoding="utf-8")
            (root / ".env").write_text("SHOULD_NOT_BE_READ", encoding="utf-8")
            (root / "private.pem").write_text("SHOULD_NOT_BE_READ", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "bad.txt").write_text("SHOULD_NOT_BE_READ", encoding="utf-8")
            resolved_root = root.resolve()
            found = {p.relative_to(resolved_root).as_posix() for p in tool.safe_files(root)}
            self.assertEqual({"safe.md"}, found)

    def test_out_of_root_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            target = Path(outside) / "outside.txt"
            target.write_text("outside", encoding="utf-8")
            link = root / "link.txt"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("symlink creation unavailable")
            self.assertEqual([], list(tool.safe_files(root)))

    def test_private_paths_secrets_and_unreviewed_urls_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_path = "/" + "Users" + "/example/private"
            unreviewed_url = "https:" + "//" + "unreviewed.invalid/path"
            fake_key = "AKIA" + "ABCDEFGHIJKLMNOP"
            (root / "bad.md").write_text(f"{private_path} and {unreviewed_url} and {fake_key}", encoding="utf-8")
            errors = tool.security_scan(root)
            self.assertTrue(any("home path" in e for e in errors))
            self.assertTrue(any("unreviewed external domain" in e for e in errors))
            self.assertTrue(any("AWS access key" in e for e in errors))

    def test_reviewed_external_urls_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ok.md").write_text("https://github.com/donuxcom/donuxcom-skills", encoding="utf-8")
            self.assertEqual([], tool.security_scan(root))

    def test_only_github_token_expression_is_allowed_in_workflows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            github_token = "$" + "{" + "{ github.token }" + "}"
            (workflows / "ok.yml").write_text(f"token: {github_token}", encoding="utf-8")
            self.assertEqual([], tool.security_scan(root))
            unresolved = "{" + "{ TODO_VALUE }" + "}"
            (workflows / "bad.yml").write_text(f"value: {unresolved}", encoding="utf-8")
            self.assertTrue(any("unresolved public placeholder" in e for e in tool.security_scan(root)))


if __name__ == "__main__":
    unittest.main()
