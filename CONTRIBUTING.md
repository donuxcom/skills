# Contributing

Fixes and focused improvements are welcome. Propose a new skill in an approved issue before implementation. A new skill must be reusable, non-overlapping, least-privilege, dependency-light, portable, documented, security-reviewed, and covered by activation and safety tests.

## Source and generated files

`skills/*/SKILL.md`, per-skill READMEs and HTML report shells, docs, tests, and `scripts/repo_tool.py` are source. `catalog.json` and `dist/` are generated. Do not hand-edit generated outputs.

## Local checks

```sh
python3 scripts/repo_tool.py validate
python3 -m unittest discover -s tests -v
python3 scripts/repo_tool.py catalog --check
python3 scripts/repo_tool.py security
python3 scripts/repo_tool.py build
python3 scripts/repo_tool.py verify
```

For the official Agent Skills baseline, use the pinned reference implementation:

```sh
uvx --from 'git+https://github.com/agentskills/agentskills@38a2ff82958afee88dadf4831509e6f7e9d8ef4e#subdirectory=skills-ref' skills-ref validate skills/dx-codebase-walkthrough
```

Repeat it for each changed skill. The repository-specific checks remain required because the reference validator does not inspect links, safety rules, generated files, or release artifacts.

Tests require Python 3.9+ and no network. Use synthetic fixtures only; never copy `.env`, credentials, private keys, production logs, customer data, or private identifiers. Behavioral cases live in `tests/fixtures/activation_cases.json` and must include at least three positive and three negative prompts per skill.

Keep diffs narrow. Explain scope, linked issue, commands and real results, security/data effects, breaking changes, and untested areas in the pull request. AI assistance may be disclosed in the PR. By contributing, you license the contribution under Apache-2.0 and certify under the Developer Certificate of Origin (`Signed-off-by`). Deprecations and breaking changes follow the release process.
