# Optional stdio MCP interface

Native Hermes integration is the primary path; see the root README. The inherited standalone adapter now targets the official Python MCP 2.x SDK. It shares the scoped tools, journal and single-writer lease, but does not provide Hermes lifecycle extraction or automatic prompt recall to other clients.

For a separate, operator-managed environment outside Hermes:

```sh
python -m venv .venv
# POSIX paths; Windows uses .venv/Scripts/python.exe.
.venv/bin/python -m pip install 'git+https://github.com/rajansanand/hermes-recall.git#egg=hermes-recall[mcp]'
.venv/bin/hermes-recall --home /path/to/separate-profile mcp
```

Configure `hermes-recall.json` and embedding credentials in that separate profile/environment before launch. Do not point this server at an embedded store currently open in Hermes or another process. Stdio stdout belongs exclusively to the MCP protocol.

Available tools: `hermes_recall_search`, `hermes_recall_add`, `hermes_recall_update`, `hermes_recall_delete`. Tool arguments cannot override profile identity or request arbitrary files. Automated tests cover real SDK initialization, CRUD, scope/path denial, sanitized errors and writer exclusion; no broad client compatibility claim is made.
