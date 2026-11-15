# Production readiness assessment

Status: **unsafe to expose as a public code-execution service in its current form**.

## Verified from the current default branch
- Streamlit app scrapes Python snippets from arbitrary URLs, resolves dependencies, creates virtual environments, installs packages, and executes snippets with subprocesses.
- The source explicitly describes the virtualenv as a sandbox, but a Python virtualenv is not an operating-system security boundary.
- The current implementation uses host subprocess execution; network is disabled by proxy configuration rather than an OS-level network namespace.
- No tests, CI workflow, dependency lockfile, or security policy was found.

## Critical release blockers
1. Run package installation and snippets only inside a hardened disposable container or equivalent OS sandbox, never under the application host's identity.
2. Enforce no network by default at the OS/container layer; add explicit, isolated opt-in networking.
3. Apply CPU, memory, process, disk, file-size, output, and wall-clock limits; run as non-root with no capabilities and a read-only root filesystem.
4. Validate and restrict target URLs to prevent SSRF, including redirects, DNS rebinding, private/link-local/loopback IPs, and non-HTTP schemes.
5. Pin/record resolved dependencies and hashes; avoid silently upgrading to arbitrary latest packages on every run.
6. Add hostile-code, archive, package-install, SSRF, timeout, and output-flood tests.

## Release gate
Do not deploy public snippet execution until a security boundary is independently tested. A subprocess timeout and virtualenv alone are insufficient.
