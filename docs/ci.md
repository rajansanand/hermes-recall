# CI

This fork uses the read-only GitHub Actions workflow in .github/workflows/ci.yml: a pinned Hermes host, isolated test environment, Ruff, canonical per-file tests, and distribution build. It requires no model or memory-service credentials and does not publish to PyPI.

Upstream scan-service gates and account-specific workflows were removed. Inherited benchmark/validation records apply only to their recorded upstream revision; see local-changes.md for this fork's scope.
