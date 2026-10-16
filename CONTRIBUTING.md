# Contributing

Independent fork: preserve upstream attribution and add behavioral regression tests for lifecycle, storage and scope changes. Tests must use temporary state and deterministic model fixtures, never a real memory store or API key.

Build an isolated test environment through a real Hermes checkout's `pm.build_env`, using that host's exported requirements, this plugin, the test dependency group and Ruff 0.15.1. Do not modify a user's managed Hermes runtime. Exact CI setup is in `.github/workflows/ci.yml`.

Run Ruff checks and formatting, then the host's canonical `scripts/run_tests.sh` with `HERMES_PYTHON` pointing at that environment. Run the plugin's tests directory with `-j 2 --file-retries 0 -- --tb=short`. The runner isolates credentials, locale and per-file Python state. Live server/cloud checks require explicit disposable service settings.

Native Hermes is the supported integration. Optional standalone stdio transport uses MCP 2.x; CI exercises real protocol clients. Upstream CI service-policy tests requiring its scan accounts were removed; inherited behavioral tests remain. Upstream validation records certify only their named revisions.

Report security issues through this repository's private vulnerability reporting when available. Never attach credentials or user memories to public issues. Keep recalled text untrusted and user/profile boundaries explicit.
