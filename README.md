# Hermes Recall

Native persistent memory for Hermes Agent: local embedded Qdrant, durable SQLite write journal, current-question semantic recall, and multiple chats sharing one store in the same gateway process.

An independent MIT-licensed derivative of [Kang Liu's Qdrant Memory for Hermes](https://github.com/cnkang/hermes-plugin-qdrant-memory), based on commit `e14adc061046b1232858d91a4e8454efbc31dbab`. Original history, copyright and license retained. See [NOTICE.md](NOTICE.md).

## Changes in this fork

- Retrieve against the **current question during native turn start**, before Hermes's fast-prefetch deadline. The prompt receives only results matching the exact query and current user scope.
- Share one reference-counted embedded backend among chats in the same profile and process. Each chat keeps its own scope, worker and extraction context. Closing one chat does not close another chat's store.
- Keep the cross-process writer lock. This is not a distributed or multi-process writer implementation.
- Allow OpenRouter provider routing preferences through the OpenAI-compatible embedding adapter.
- Use an optional MCP 2.x adapter compatible with current Hermes dependencies. Native Hermes remains the primary integration; see [docs/mcp.md](docs/mcp.md) for the separate stdio interface.

## Installation

Requires Hermes Agent with the native MemoryProvider lifecycle; locally exercised against Hermes `9085061a8ce1de3cb115534fcfae6b5d01be76fc` on Windows/Python 3.14. Other platforms/releases require validation.

```sh
hermes plugins install rajansanand/hermes-recall --enable --yes-deps
hermes memory setup
# Select hermes-recall, then configure its backend and embeddings.
hermes config set memory.provider hermes-recall
hermes hermes-recall init --existing use
```

Use Hermes's dependency manager; do not pip-install into its managed runtime. Start a new conversation after configuration changes. Installing alongside the original provider does not migrate its data: this fork uses its own `hermes-recall.json` and `hermes-recall/` directory.

## Local storage with OpenRouter embeddings

Put the API key in your active profile's `.env`; never commit it:

```dotenv
OPENROUTER_API_KEY=your_key_here
```

Save `hermes-recall.json` in that same profile:

```json
{
  "schema_version": 1,
  "scope": {"user_id": "hermes-user", "agent_id": "hermes"},
  "qdrant": {"mode": "embedded", "collection": "hermes_recall"},
  "llm": {"mode": "inherit", "task": "hermes_recall_extraction"},
  "embedding": {
    "mode": "plugin",
    "provider": "openai-compatible",
    "base_url": "https://openrouter.ai/api/v1",
    "model": "qwen/qwen3-embedding-8b",
    "dimensions": 4096,
    "api_key_env": "OPENROUTER_API_KEY",
    "timeout_seconds": 30,
    "provider_preferences": {"sort": "latency"}
  },
  "search": {"top_k": 3, "candidate_k": 12, "min_score": 0.45}
}
```

The score threshold is a starting example, not a universal accuracy guarantee. Calibrate on your own facts and queries. Embedding model or dimension changes require a new compatible collection and explicit migration.

For primary semantic memory with small automatic context, merge these settings into `config.yaml`:

```yaml
memory:
  provider: hermes-recall
  memory_enabled: false
  user_profile_enabled: false
  prefetch_spill_enabled: true
hooks:
  output_spill:
    max_chars: 3200
    preview_head: 2200
    preview_tail: 0
```

The host spills oversized recall to a local file with a bounded preview. Four scoped tools are available: `hermes_recall_search`, `hermes_recall_add`, `hermes_recall_update`, `hermes_recall_delete`. Use targeted search when automatic recall is absent or incomplete.

## Automatic capture and data flow

After each admitted primary-agent turn, a durable SQLite journal records work for background fact extraction and embedding. Extraction uses Hermes's configured LLM facade; it can inherit the session model. Session-end and pre-compression hooks preserve additional evidence. Successful work is scrubbed from journal payloads; pending/failed work remains for recovery.

Storage is local in embedded mode, but **memory/query text goes to the configured embedding endpoint**, and conversation text goes to the configured extraction model. OpenRouter API usage is billed separately from chat subscriptions. Local Ollama embeddings remain supported through the inherited configuration.

## Limits and operations

- Remote recall can add seconds before a reply; observed local setup calls ranged roughly 2–17 seconds. API timeouts and write contention can still skip automatic recall. Keep explicit search tools available.
- Same-process chats share storage. Separate processes/profiles must not concurrently write the same destination. Stop the gateway before embedded-store maintenance or backup.
- Durability starts after Hermes delivers the callback and the plugin journals it. Forced exit before host delivery can lose unadmitted work.
- Corrections can coexist with historical facts; prefer explicit later corrections. Extraction and deduplication are model-dependent.
- This fork is experimental. No blanket platform, recall-accuracy, or production-readiness claim.

```sh
hermes hermes-recall status
hermes hermes-recall doctor
hermes hermes-recall list
# Stop the gateway before mutating maintenance:
hermes gateway stop
hermes hermes-recall retry
```

## Development and provenance

See [CONTRIBUTING.md](CONTRIBUTING.md) for isolated testing, [docs/local-changes.md](docs/local-changes.md) for fork validation, and upstream documentation for inherited storage/recovery semantics. Existing upstream validation records describe their recorded revisions, not certification of this fork.

License: [MIT](LICENSE). No hosted memory subscription required; configured model/API services may charge usage fees.
