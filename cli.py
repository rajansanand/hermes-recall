"""Hermes directory-provider CLI discovery seam."""

from .hermes_recall.cli import main
from .hermes_recall.cli import register_cli as register_cli

globals()["hermes-recall_command"] = main
