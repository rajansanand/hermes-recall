"""Real Hermes discovery, CLI dry-run and LLM routing contracts."""

import argparse
import json
import logging

from plugins.memory import discover_plugin_cli_commands, find_provider_dir, load_memory_provider

from hermes_recall.cli import register_cli, run
from hermes_recall.extraction import Extractor

from .helpers import LLM, copy_plugin


def test_real_directory_discovery_and_cli(tmp_path, monkeypatch, caplog):
    """Verify real directory discovery and cli."""
    home = tmp_path / "home"
    (home / "plugins").mkdir(parents=True)
    copy_plugin(home / "plugins" / "hermes-recall")
    (home / "config.yaml").write_text(
        "memory:\n  provider: hermes-recall\nplugins:\n  isolation: in_process\n"
    )
    monkeypatch.setenv("HERMES_HOME", str(home))
    assert find_provider_dir("hermes-recall") == home / "plugins" / "hermes-recall"
    with caplog.at_level(logging.DEBUG):
        provider = load_memory_provider("hermes-recall")
    assert provider is not None, caplog.text
    assert provider.name == "hermes-recall"
    assert provider.context.llm is not None
    assert {s["name"] for s in provider.get_tool_schemas()} == {
        "hermes_recall_search",
        "hermes_recall_add",
        "hermes_recall_update",
        "hermes_recall_delete",
    }
    commands = discover_plugin_cli_commands()
    assert any(c["name"] == "hermes-recall" for c in commands)
    command = next(c for c in commands if c["name"] == "hermes-recall")
    parser = argparse.ArgumentParser()
    command["setup_fn"](parser)
    assert command["handler_fn"](parser.parse_args(["status"])) == 0


def test_dry_run_has_no_target_or_ledger_writes(tmp_path):
    """Verify dry run has no target or ledger writes."""
    source = tmp_path / "export.json"
    source.write_text(json.dumps([{"id": "one", "memory": "cats preferred"}]))
    parser = argparse.ArgumentParser()
    register_cli(parser)
    args = parser.parse_args(["migrate", "mem0", "--source-json", str(source), "--dry-run"])
    result = run(args, home=tmp_path / "home")
    assert result["source_unique_count"] == 1
    assert not (tmp_path / "home").exists()


def test_llm_inherit_and_task_routing():
    """Verify llm inherit and task routing."""
    llm = LLM()
    event = {"user": "cats", "assistant": "ack"}
    Extractor(llm, {"mode": "inherit"}).extract(event)
    assert not any(k in llm.calls[-1] for k in ("task", "provider", "model"))
    Extractor(llm, {"mode": "task", "task": "hermes_recall_extraction"}).extract(event)
    assert llm.calls[-1]["task"] == "hermes_recall_extraction"
