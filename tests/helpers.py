"""Deterministic service fixtures backed by real Qdrant and SQLite components."""

from types import SimpleNamespace

from qdrant_client import QdrantClient

from hermes_recall.config import DEFAULTS, merge
from hermes_recall.extraction import Extractor
from hermes_recall.ledger import Ledger
from hermes_recall.qdrant_store import QdrantStore
from hermes_recall.runtime import Runtime


def copy_plugin(target):
    """Install source files like the native installer, without symlink privileges."""
    from pathlib import Path
    from shutil import copy2, copytree, ignore_patterns

    source = Path(__file__).resolve().parents[1]
    target.mkdir()
    for name in (
        "__init__.py",
        "cli.py",
        "config_schema.py",
        "plugin.yaml",
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "NOTICE.md",
    ):
        copy2(source / name, target / name)
    copytree(
        source / "hermes_recall", target / "hermes_recall", ignore=ignore_patterns("__pycache__")
    )


def capture_committed_event_payloads(monkeypatch, ledger):
    """Capture event bodies at acknowledgement before retention scrubs them."""
    import json

    captured = []
    finish = ledger.finish

    def capture(table, key, status="COMMITTED"):
        """Snapshot a committed event immediately before its durable body is scrubbed."""
        if table == "events" and status == "COMMITTED":
            row = ledger.row("events", key)
            if row:
                captured.append(json.loads(row["payload_json"]))
        return finish(table, key, status)

    monkeypatch.setattr(ledger, "finish", capture)
    return captured


class Embedder:
    """Provide deterministic three-dimensional vectors for behavior contracts."""

    dimensions = 3
    fingerprint = "test-embedding-space-v1"

    def embed_documents(self, texts):
        """Embed fixture texts in input order."""
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        # Fixed, interpretable embedding fixture: three unrelated topics.
        """Map fixture topics to deterministic unit vectors."""
        if "cat" in text.lower():
            return [1.0, 0.0, 0.0]
        if "dog" in text.lower():
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]


class LLM:
    """Return controlled structured LLM responses and capture routing options."""

    def __init__(self, relation="UNRELATED"):
        """Initialize the relation decision and captured-call list."""
        self.calls = []
        self.relation_value = relation

    def complete_structured(self, **kwargs):
        """Return fixture facts or the configured relation without contacting a model."""
        import json

        self.calls.append(kwargs)
        if kwargs["purpose"].endswith("relation"):
            return SimpleNamespace(parsed={"relation": self.relation_value})
        turn = json.loads(kwargs["input"][0]["text"])
        return SimpleNamespace(
            parsed={
                "memories": [{"text": turn["user"], "category": ["preference"], "importance": 0.8}]
            }
        )


def config(**overrides):
    """Merge compact test defaults with scenario-specific settings."""
    return merge(
        merge(
            DEFAULTS,
            {
                "embedding": {"dimensions": 3},
                "write": {"backoff_base_seconds": 0, "backoff_max_seconds": 0},
            },
        ),
        overrides,
    )


def runtime(home, client=None, cfg=None, llm=None, ledger_namespace=None):
    """Build a real Qdrant store and ledger with deterministic injected services."""
    cfg = cfg or config()
    client = client or QdrantClient(":memory:")
    store = QdrantStore(client, cfg, Embedder())
    store.initialize()
    return Runtime(
        cfg,
        store,
        Ledger(home, ledger_namespace or store.collection),
        Extractor(llm or LLM(), cfg["llm"]),
    )
