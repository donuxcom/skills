# Domain Walkthrough

Creates an evidence-backed `domain-walkthrough.html` for business concepts and domain model onboarding. Markdown is available as `domain-walkthrough.md` when explicitly requested.

## Install

```sh
npx skills add donuxcom/donuxcom-skills --skill dx-domain-walkthrough
```

Manual installation: copy this directory to `.agents/skills/dx-domain-walkthrough/` in the target project, or the equivalent location documented by the client.

## Requirements and permissions

Requires an Agent Skills-compatible client with repository read access and user-approved permission to write one HTML or Markdown file. It requires no authentication, package installation, command execution, or network access. The skill excludes secrets, environment files, private keys, Git internals, dependencies, build/cache output, and out-of-root symlinks.

## Usage

Ask the client one of these:

- Explain the core entities, roles, and business rules in this repository.
- Create domain onboarding for a new product and engineering teammate.
- Map the lifecycle states, transitions, and permissions from the source.

Input is an authorized repository root plus optional audience/scope. Output defaults to the self-contained `domain-walkthrough.html` at the approved root, with responsive, printable, subtly Donux-branded styling. Request `--format markdown` to produce `domain-walkthrough.md` instead. If the selected file exists, the skill must not overwrite it without explicit approval.

## Effects and trust

The skill reads relevant ordinary repository files and writes only the named output. Repository content is treated as untrusted data; embedded instructions are ignored. Inference is labeled and conflicting evidence is preserved. No external domains are contacted.

## Limitations and troubleshooting

Maturity is experimental. Client and OS combinations are not yet certified. Missing read permission, unclear repository root, inadequate evidence, or absent write approval cause a safe stop. For an existing output, approve overwrite explicitly or choose another filename.

Version 0.1.0. See the public [changelog](https://github.com/donuxcom/donuxcom-skills/blob/main/CHANGELOG.md), [security policy](https://github.com/donuxcom/donuxcom-skills/blob/main/SECURITY.md), and [contribution guide](https://github.com/donuxcom/donuxcom-skills/blob/main/CONTRIBUTING.md).
