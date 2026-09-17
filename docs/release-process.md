# Release Process

1. Confirm IP ownership and Apache-2.0 relicensing authority; obtain a second human disclosure review.
2. Set one collection version consistently in skill metadata, catalog, and changelog.
3. Run all local verification commands from `CONTRIBUTING.md`, including the pinned official `skills-ref` validation command for every skill.
4. Inspect every archive entry and checksum; install into a clean temporary project; test update approval, removal, and rollback.
5. Enable and test GitHub private vulnerability reporting, configure CODEOWNERS and protected branches, and obtain release approval.
6. Create a protected immutable semantic-version tag and GitHub Release only after all gates pass. Attach archives and `SHA256SUMS`; do not publish mutable `main` artifacts.

The tag-only release workflow enforces the deterministic gates and uploads the three archives plus checksums. Before tagging, a maintainer must also run the behavioral evaluation plan with and without each skill, record the client/model/commit and sanitized evidence, and obtain release approval. Scheduled `security.yml` and `evals.yml` runs provide the dependency-free static census; they do not replace human disclosure review or model-based behavioral evaluation.

Patch releases fix compatible behavior; minor releases add compatible capabilities; major releases remove or rename skills or materially change permissions/output contracts. Deprecations are documented before removal except for urgent security withdrawal.
