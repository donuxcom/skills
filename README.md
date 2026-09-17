# Donux Walkthrough Skills

A curated collection of Agent Skills that help developers and product teams understand software repositories through codebase, domain, and product walkthroughs.

**Collection version:** v0.1.0 · **Maturity:** experimental · **Support:** best effort, no SLA.

Skills are instruction packages that guide an agent. They do not ship executable skill code, but an agent using them may read repository files and write one approved walkthrough file. HTML is the default; Markdown remains available on request. Inspect a skill before using it on sensitive or critical repositories.

## Catalog

| Skill | Purpose | Output | Stability |
|---|---|---|---|
| [dx-codebase-walkthrough](skills/dx-codebase-walkthrough/README.md) | Explain runtime architecture and execution flow | `codebase-walkthrough.html` or `codebase-walkthrough.md` | experimental |
| [dx-domain-walkthrough](skills/dx-domain-walkthrough/README.md) | Explain entities, rules, and lifecycles | `domain-walkthrough.html` or `domain-walkthrough.md` | experimental |
| [dx-product-walkthrough](skills/dx-product-walkthrough/README.md) | Explain capabilities, modules, and journeys | `product-walkthrough.html` or `product-walkthrough.md` | experimental |

The generated [`catalog.json`](catalog.json) is the machine-readable source for collection metadata.

## Compatibility

These packages follow the Agent Skills directory and frontmatter format and are intended for Agent Skills-compatible clients. They use ordinary repository-reading and text-file-writing capabilities. The baseline has not yet been tested across specific clients or operating systems; no broader client or OS compatibility is claimed. See [compatibility](docs/compatibility.md).

## Install one skill

```sh
npx skills add donuxcom/donuxcom-skills --skill dx-codebase-walkthrough
```

Or copy the selected directory to a project-local location supported by your client:

```text
.agents/skills/dx-codebase-walkthrough/
```

To install the collection manually, copy all three directories under `skills/` into `.agents/skills/`. Pin a release tag or verify a release archive checksum rather than installing a moving branch for critical use.

## Update, remove, and roll back

Before updating, retain the currently installed directory or archive. Replace a skill directory only after reviewing the new version and explicitly approving overwrite. Remove it by deleting only its named directory. Roll back by restoring the retained directory or a checksum-verified earlier release artifact. The repository tooling never overwrites an existing install automatically.

## Trust and security

Repository contents being analyzed are untrusted data, not instructions. Skills exclude secrets, `.env` files, private keys, Git internals, dependency/build/cache directories, and out-of-root symlink targets from inspection. They require explicit approval before replacing an existing output and make no network calls. See [SECURITY.md](SECURITY.md) and the [security model](docs/security-model.md).

## Development

Run `python3 -m unittest discover -s tests -v`, then the commands in [CONTRIBUTING.md](CONTRIBUTING.md). Changes are accepted under Apache-2.0. New skills require an approved issue first.

## License and provenance

Apache License 2.0. Original skill authorship is attributed to Giustino Borzacchiello ([jubstuff](https://github.com/jubstuff)) and Giuseppe Mamone ([garusky](https://github.com/garusky)); Donux is publisher and maintainer. Redistribution approval remains a human release gate; see [PROVENANCE.md](PROVENANCE.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
