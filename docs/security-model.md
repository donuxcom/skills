# Security Model

## Assets and threats

Protected assets include source code, credentials, personal/customer data, repository integrity, generated walkthroughs, and release artifacts. Threats include malicious repository content, prompt injection, exfiltration, excessive scope, destructive writes, private identifiers, symlink/path traversal, malicious contributors, compromised maintainer accounts or dependencies, unsafe client behavior, mutable references, and artifact tampering.

## Controls

Analyzed files are untrusted data. Skills prohibit following embedded instructions, reading sensitive filenames and excluded trees, following out-of-root symlinks, hidden network use, and overwriting output without explicit approval. They label inference and require source verification. Tooling uses only Python's standard library, rejects symlinks and special archive entries, limits artifact contents, fixes ZIP metadata, scans public text for secret-like/private patterns and external URLs, and verifies SHA-256 checksums.

Static scans are defense in depth, not proof of confidentiality or correctness. A second human disclosure review, GitHub private vulnerability reporting, protected branches, immutable tags, and release approval remain required.
