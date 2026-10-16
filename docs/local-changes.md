# Fork validation

This fork starts from upstream `e14adc061046b1232858d91a4e8454efbc31dbab`. Real local setup checks exercised automatic user-fact extraction, a failed request retained in the journal followed by retry/restart replay, fresh-session semantic recall, later explicit correction recall, bounded context spilling, user isolation, same-process shared ownership, sibling shutdown, reopen persistence, and separate-process writer exclusion.

These were setup acceptance checks on Windows/Python 3.14 with a real Hermes host and Qwen embeddings via OpenRouter. They are not a broad benchmark. No personal transcripts, credentials, machine paths, or memory stores accompany this repository. Deterministic regression tests cover the changed lifecycle and ownership behavior; public CI results are reported separately.

Release preparation on Windows/Python 3.14: canonical Hermes runner completed 336 tests passed, 9 skipped, 0 failed across 37 files. Skips cover optional live service/platform cases. Ruff lint/format checks and wheel/source-distribution builds passed; package audit confirmed license/notice files and no private state. Installed standalone tests exercised the updated optional MCP 2 adapter. GitHub CI results are independent of these local results.
