"""Current-question recall through the real Hermes lifecycle, with deterministic services."""

import json
from threading import Event, Thread
from types import SimpleNamespace

import pytest
from agent.memory_manager import MemoryManager

from hermes_recall.provider import QdrantMemoryProvider

from .helpers import LLM, Embedder, config


def make_provider(home, session="fresh", user="alice", **settings):
    """Open real embedded storage with scoped deterministic model services."""
    p = QdrantMemoryProvider(
        plugin_context=SimpleNamespace(llm=LLM()),
        embedder=Embedder(),
        overrides=config(search={"min_score": 0.8}, **settings),
    )
    p.initialize(session, hermes_home=str(home), user_id=user)
    assert p.wait_idle()
    return p


def add(p, text):
    """Require a successful explicitly authorized write."""
    result = json.loads(p.handle_tool_call("hermes_recall_add", {"text": text}))
    assert "error" not in result


def test_first_question_topic_switch_and_irrelevant_query(tmp_path):
    """Native turn start supplies matching facts before first reply, without stale reuse."""
    p = make_provider(tmp_path)
    manager = MemoryManager()
    manager.add_provider(p)
    try:
        add(p, "cats preferred")
        add(p, "dogs avoided")
        manager.on_turn_start(1, "cats", author_id="alice")
        first = manager.prefetch_all("cats", session_id="fresh")
        assert "cats preferred" in first and "dogs avoided" not in first
        assert manager.prefetch_all("dogs", session_id="fresh") == ""
        manager.on_turn_start(2, "dogs", author_id="alice")
        second = manager.prefetch_all("dogs", session_id="fresh")
        assert "dogs avoided" in second and "cats preferred" not in second
        manager.on_turn_start(3, "unrelated astronomy", author_id="alice")
        assert manager.prefetch_all("unrelated astronomy", session_id="fresh") == ""
    finally:
        manager.shutdown_all()


def test_author_change_rejects_inflight_results(tmp_path, monkeypatch):
    """A result cannot be delivered after the active session changes user."""
    p = make_provider(tmp_path)
    entered, release = Event(), Event()
    search = p.store.search

    def blocked_search(*args, **kwargs):
        """Expose the user-scope transition while scoped retrieval is running."""
        entered.set()
        assert release.wait(5)
        return search(*args, **kwargs)

    add(p, "cats preferred")
    monkeypatch.setattr(p.store, "search", blocked_search)
    worker = Thread(target=p.on_turn_start, args=(1, "cats"), kwargs={"author_id": "alice"})
    try:
        worker.start()
        assert entered.wait(5)
        p.on_turn_start(2, "", author_id="bob")
        release.set()
        worker.join(5)
        assert not worker.is_alive()
        assert p.prefetch("cats") == ""
    finally:
        release.set()
        worker.join(5)
        p.shutdown()


def test_shared_chats_keep_scope_and_survive_sibling_close(tmp_path):
    """Shared ownership does not share user authority or close a sibling's client."""
    a = make_provider(tmp_path, session="a", user="alice")
    b = make_provider(tmp_path, session="b", user="bob")
    try:
        assert a.store is b.store and a.runtime.lock is b.runtime.lock
        add(a, "cats preferred")
        b.on_turn_start(1, "cats", author_id="bob")
        assert b.prefetch("cats") == ""
        a.shutdown()
        add(b, "dogs preferred")
        b.on_turn_start(2, "dogs", author_id="bob")
        assert "dogs preferred" in b.prefetch("dogs")
    finally:
        a.shutdown()
        b.shutdown()
    reopened = make_provider(tmp_path, session="new", user="bob")
    try:
        reopened.on_turn_start(1, "dogs", author_id="bob")
        assert "dogs preferred" in reopened.prefetch("dogs")
    finally:
        reopened.shutdown()


def test_changed_live_settings_fail_without_breaking_owner(tmp_path):
    """An incompatible borrower cannot replace a live backend or its settings."""
    owner = make_provider(tmp_path)
    contender = QdrantMemoryProvider(
        plugin_context=SimpleNamespace(llm=LLM()),
        embedder=Embedder(),
        overrides=config(search={"min_score": 0.8, "top_k": 4}),
    )
    try:
        with pytest.raises(RuntimeError, match="settings changed"):
            contender.initialize("changed", hermes_home=str(tmp_path))
        add(owner, "cats preferred")
        owner.on_turn_start(1, "cats", author_id="alice")
        assert "cats preferred" in owner.prefetch("cats")
    finally:
        owner.shutdown()
