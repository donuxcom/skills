# Architecture

`skills/` is the canonical collection. Each package contains Agent Skills-compatible `SKILL.md` instructions, a human `README.md`, and a shared-shape `templates/report-shell.html` baseline for standalone HTML output. There is no runtime framework and no network dependency.

`scripts/repo_tool.py` is a deterministic Python-standard-library tool with validation, catalog, security scan, artifact build, and artifact verification commands. `catalog.json` is generated from skill frontmatter. Tests exercise metadata, references, activation boundaries, safety contracts, scanning, and packaging. `dist/` is disposable generated output.

The collection releases as one semantic version. Release archives contain one skill directory, including its HTML report shell, plus the root license and provenance notice; ZIP timestamps, ordering, compression, and permissions are fixed for reproducibility.
