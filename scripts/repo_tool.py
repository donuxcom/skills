#!/usr/bin/env python3
"""Deterministic repository validation and packaging (stdlib only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
DIST = ROOT / "dist"
VERSION = "0.1.0"
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "coverage", "__pycache__", ".cache", ".venv", "venv"}
SENSITIVE_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
REQUIRED_ROOT = {
    "README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
    "AGENTS.md", "CHANGELOG.md", "PROVENANCE.md", "THIRD_PARTY_NOTICES.md", "catalog.json",
    "docs/architecture.md", "docs/compatibility.md", "docs/security-model.md", "docs/release-process.md",
}
REQUIRED_SECTIONS = {
    "## When to use", "## Input contract", "## Prerequisites and exclusions", "## Procedure",
    "## Safety and approval gates", "## Output contract", "## Failure handling", "## Verification", "## References",
}
ALLOWED_DOMAINS = {
    "www.apache.org", "github.com", "www.contributor-covenant.org", "keepachangelog.com", "creativecommons.org",
}
URL_RE = re.compile(r"https?://([^/\s)\]>]+)", re.I)
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SECRET_PATTERNS = {
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "authorization header": re.compile(r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    "generic secret assignment": re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token)\s*[=:]\s*['\"][^'\"\s]{12,}['\"]"),
}
PRIVATE_PATTERNS = {
    "macOS home path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "Linux home path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "private IPv4": re.compile(r"\b(?:10\.\d{1,3}|192\.168\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3})\.\d{1,3}\b"),
}
UNRESOLVED_RE = re.compile(r"(?:\{\{[^}]+\}\}|<(?:owner|repo|todo|email|your[-_ ][^>]+)>|\bTBD\b)", re.I)


def is_sensitive(path: Path) -> bool:
    name = path.name.lower()
    return name in SENSITIVE_NAMES or path.suffix.lower() in SENSITIVE_SUFFIXES


def safe_files(root: Path):
    """Yield ordinary files under root without sensitive/excluded trees or symlink traversal."""
    root = root.resolve()
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept = []
        for name in sorted(dirs):
            p = current_path / name
            if name in SKIP_DIRS or p.is_symlink():
                continue
            kept.append(name)
        dirs[:] = kept
        for name in sorted(files):
            p = current_path / name
            if p.is_symlink() or is_sensitive(p):
                continue
            try:
                p.resolve().relative_to(root)
            except ValueError:
                continue
            if p.is_file():
                yield p


def parse_frontmatter(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: frontmatter must start at byte zero")
    try:
        raw, body = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError(f"{path}: missing frontmatter terminator") from exc
    data: dict[str, object] = {}
    current_mapping = None
    for number, line in enumerate(raw.splitlines(), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  "):
            if current_mapping != "metadata" or ":" not in line:
                raise ValueError(f"{path}:{number}: unsupported YAML structure")
            key, value = line.strip().split(":", 1)
            value = value.strip().strip('"').strip("'")
            metadata = data.setdefault("metadata", {})
            assert isinstance(metadata, dict)
            metadata[key] = value
            continue
        if ":" not in line:
            raise ValueError(f"{path}:{number}: malformed frontmatter")
        key, value = line.split(":", 1)
        value = value.strip()
        if value:
            data[key] = value.strip('"').strip("'")
            current_mapping = None
        else:
            data[key] = {}
            current_mapping = key
    return data, body


def skill_dirs(skills_dir: Path = SKILLS) -> list[Path]:
    if not skills_dir.is_dir():
        raise ValueError(f"skills directory not found: {skills_dir}")
    result = [p for p in skills_dir.iterdir() if p.is_dir() and not p.is_symlink()]
    return sorted(result, key=lambda p: p.name)


def validate_skill(path: Path) -> list[str]:
    errors: list[str] = []
    if path.is_symlink() or not path.is_dir():
        return [f"{path}: skill must be a real directory"]
    skill_file = path / "SKILL.md"
    readme = path / "README.md"
    report_shell = path / "templates" / "report-shell.html"
    if not skill_file.is_file():
        return [f"{path}: missing SKILL.md"]
    if not readme.is_file():
        errors.append(f"{path}: missing README.md")
    if not report_shell.is_file():
        errors.append(f"{path}: missing templates/report-shell.html")
    try:
        meta, body = parse_frontmatter(skill_file)
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]
    allowed = {"name", "description", "license", "compatibility", "metadata"}
    extra = set(meta) - allowed
    if extra:
        errors.append(f"{skill_file}: unsupported frontmatter fields: {sorted(extra)}")
    name = meta.get("name")
    if name != path.name or not isinstance(name, str) or not NAME_RE.fullmatch(name) or len(name) > 64:
        errors.append(f"{skill_file}: name must match its valid directory name")
    desc = meta.get("description")
    if not isinstance(desc, str) or not desc or len(desc) > 1024 or "Use when" not in desc:
        errors.append(f"{skill_file}: description must state activation and fit 1024 characters")
    if meta.get("license") != "Apache-2.0":
        errors.append(f"{skill_file}: license must be Apache-2.0")
    if not isinstance(meta.get("compatibility"), str) or not meta.get("compatibility"):
        errors.append(f"{skill_file}: compatibility must be a string")
    md = meta.get("metadata")
    required_md = {"author": "Giustino Borzacchiello (jubstuff), Giuseppe Mamone (garusky)", "publisher": "Donux", "version": VERSION, "maturity": "experimental"}
    if not isinstance(md, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in md.items()):
        errors.append(f"{skill_file}: metadata keys and values must be strings")
    elif any(md.get(k) != v for k, v in required_md.items()):
        errors.append(f"{skill_file}: metadata missing or inconsistent: {required_md}")
    for section in sorted(REQUIRED_SECTIONS):
        if section not in body:
            errors.append(f"{skill_file}: missing section {section}")
    if len(skill_file.read_text(encoding="utf-8")) > 100_000:
        errors.append(f"{skill_file}: exceeds 100000 characters")
    # Resolve local Markdown links; fragments and absolute URLs are not local references.
    for file in (skill_file, readme):
        if not file.is_file():
            continue
        text = file.read_text(encoding="utf-8")
        for link in re.findall(r"\[[^]]*\]\(([^)]+)\)", text):
            target = link.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (file.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{file}: link escapes repository: {link}")
                continue
            if not resolved.exists():
                errors.append(f"{file}: broken relative link: {link}")
    return errors


def validate(skills_dir: Path = SKILLS, require_root: bool = True) -> list[str]:
    errors: list[str] = []
    dirs = skill_dirs(skills_dir)
    if not dirs:
        errors.append(f"{skills_dir}: no skills found")
    names = [p.name for p in dirs]
    if len(names) != len(set(names)):
        errors.append("duplicate skill names")
    for path in dirs:
        errors.extend(validate_skill(path))
    if require_root:
        for relative in sorted(REQUIRED_ROOT):
            if not (ROOT / relative).is_file():
                errors.append(f"missing required root file: {relative}")
        workflow = ROOT / ".github" / "workflows" / "ci.yml"
        if workflow.is_file():
            for number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
                if "uses:" in line and not re.search(r"uses:\s+[^@\s]+@[0-9a-f]{40}(?:\s|$)", line):
                    errors.append(f"{workflow}:{number}: GitHub Action must be pinned to a full commit SHA")
    return errors


def catalog_data() -> dict[str, object]:
    skills = []
    for path in skill_dirs():
        meta, _ = parse_frontmatter(path / "SKILL.md")
        md = meta["metadata"]
        assert isinstance(md, dict)
        skills.append({
            "name": meta["name"], "version": md["version"], "description": meta["description"],
            "maturity": md["maturity"], "license": meta["license"], "compatibility": meta["compatibility"],
            "author": md["author"], "publisher": md["publisher"], "external_domains": [],
            "permissions": ["read-approved-repository-files", "write-one-approved-walkthrough-output"],
            "output_formats": ["html", "markdown"], "default_output_format": "html",
            "deprecated": False,
        })
    return {"schema_version": "1", "collection_version": VERSION, "maturity": "experimental", "skills": skills}


def catalog_text() -> str:
    return json.dumps(catalog_data(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def security_scan(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in list(dirs):
            if (current_path / name).is_symlink():
                errors.append(f"symlink directory not allowed: {(current_path / name).relative_to(root)}")
                dirs.remove(name)
        for name in sorted(files):
            path = current_path / name
            rel = path.relative_to(root)
            if path.is_symlink():
                errors.append(f"symlink file not allowed: {rel}")
                continue
            if is_sensitive(path):
                errors.append(f"sensitive filename not allowed: {rel}")
                continue
            if not path.is_file():
                errors.append(f"special file not allowed: {rel}")
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"unexpected binary file: {rel}")
                continue
            for label, pattern in {**SECRET_PATTERNS, **PRIVATE_PATTERNS}.items():
                if pattern.search(text):
                    errors.append(f"{rel}: possible {label}")
            placeholder_text = text
            if rel.parts[:2] == (".github", "workflows"):
                placeholder_text = re.sub(r"\$\{\{\s*github\.token\s*\}\}", "", placeholder_text)
            if UNRESOLVED_RE.search(placeholder_text):
                errors.append(f"{rel}: unresolved public placeholder")
            for domain in URL_RE.findall(text):
                domain = domain.lower().rstrip(".")
                if domain not in ALLOWED_DOMAINS:
                    errors.append(f"{rel}: unreviewed external domain {domain}")
    return errors


def zip_entry(name: str, data: bytes) -> tuple[zipfile.ZipInfo, bytes]:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info, data


def build() -> list[Path]:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    built: list[Path] = []
    for skill in skill_dirs():
        archive = DIST / f"{skill.name}-{VERSION}.zip"
        entries = [
            (f"{skill.name}/SKILL.md", (skill / "SKILL.md").read_bytes()),
            (f"{skill.name}/README.md", (skill / "README.md").read_bytes()),
            (f"{skill.name}/templates/report-shell.html", (skill / "templates" / "report-shell.html").read_bytes()),
            ("LICENSE", (ROOT / "LICENSE").read_bytes()),
            ("PROVENANCE.md", (ROOT / "PROVENANCE.md").read_bytes()),
            ("THIRD_PARTY_NOTICES.md", (ROOT / "THIRD_PARTY_NOTICES.md").read_bytes()),
        ]
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for name, data in sorted(entries):
                info, payload = zip_entry(name, data)
                zf.writestr(info, payload, compresslevel=9)
        built.append(archive)
    manifest = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in built)
    (DIST / "SHA256SUMS").write_text(manifest, encoding="utf-8")
    return built


def verify() -> list[str]:
    errors: list[str] = []
    manifest_path = DIST / "SHA256SUMS"
    if not manifest_path.is_file():
        return ["dist/SHA256SUMS missing"]
    expected = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        expected[name] = digest
    wanted = {f"{p.name}-{VERSION}.zip" for p in skill_dirs()}
    if set(expected) != wanted:
        errors.append(f"checksum manifest mismatch: expected {sorted(wanted)}, got {sorted(expected)}")
    for name, digest in sorted(expected.items()):
        archive = DIST / name
        if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
            errors.append(f"checksum mismatch: {name}")
            continue
        skill_name = name[: -len(f"-{VERSION}.zip")]
        allowed = {
            f"{skill_name}/SKILL.md", f"{skill_name}/README.md",
            f"{skill_name}/templates/report-shell.html", "LICENSE",
            "PROVENANCE.md", "THIRD_PARTY_NOTICES.md",
        }
        with zipfile.ZipFile(archive) as zf:
            names = set(zf.namelist())
            if names != allowed:
                errors.append(f"{name}: unsafe or unexpected entries: {sorted(names ^ allowed)}")
            for info in zf.infolist():
                pure = PurePosixPath(info.filename)
                mode = (info.external_attr >> 16) & 0o170000
                if pure.is_absolute() or ".." in pure.parts or "\\" in info.filename:
                    errors.append(f"{name}: unsafe path {info.filename}")
                if mode != 0o100000:
                    errors.append(f"{name}: non-regular entry {info.filename}")
                if info.date_time != (1980, 1, 1, 0, 0, 0):
                    errors.append(f"{name}: non-deterministic timestamp {info.filename}")
            with tempfile.TemporaryDirectory() as tmp:
                zf.extractall(tmp)
                errors.extend(validate_skill(Path(tmp) / skill_name))
    return errors


def print_result(label: str, errors: list[str]) -> int:
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"{label}: FAIL ({len(errors)} errors)", file=sys.stderr)
        return 1
    print(f"{label}: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--skills-dir", type=Path, default=SKILLS)
    v.add_argument("--no-root", action="store_true")
    vs = sub.add_parser("validate-skill")
    vs.add_argument("path", type=Path)
    c = sub.add_parser("catalog")
    c.add_argument("--check", action="store_true")
    sub.add_parser("security")
    sub.add_parser("build")
    sub.add_parser("verify")
    args = parser.parse_args()
    if args.command == "validate":
        return print_result("validation", validate(args.skills_dir, not args.no_root))
    if args.command == "validate-skill":
        return print_result("skill validation", validate_skill(args.path))
    if args.command == "catalog":
        generated = catalog_text()
        path = ROOT / "catalog.json"
        if args.check:
            return print_result("catalog freshness", [] if path.is_file() and path.read_text(encoding="utf-8") == generated else ["catalog.json is stale; run catalog without --check"])
        path.write_text(generated, encoding="utf-8")
        print("catalog: wrote catalog.json")
        return 0
    if args.command == "security":
        return print_result("security scan", security_scan())
    if args.command == "build":
        archives = build()
        print(f"artifact build: PASS ({len(archives)} archives)")
        return 0
    if args.command == "verify":
        return print_result("artifact verification", verify())
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
