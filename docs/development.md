# Development

Use the isolated dependency-manager setup in CONTRIBUTING.md and the pinned example in .github/workflows/ci.yml. Run Ruff, the real Hermes canonical test runner and a distribution build before publishing. Native tests use deterministic embedding/LLM fixtures and temporary storage; optional server/cloud tests require explicit disposable service arguments.

Optional standalone stdio transport uses MCP 2.x. No model API keys are needed for standard checks. The package's public identity, module and tools are hermes-recall / hermes_recall; the original project remains credited in NOTICE.md.
