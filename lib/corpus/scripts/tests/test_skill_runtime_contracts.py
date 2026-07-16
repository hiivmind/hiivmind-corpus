"""Instruction-contract tests for resolved corpus status execution."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
STATUS_SKILL = ROOT / "skills/hiivmind-corpus-status/SKILL.md"
HEADLESS_STATUS_SKILL = ROOT / "skills/hiivmind-corpus-status-headless/SKILL.md"


def test_interactive_status_checks_resolved_context_before_registry():
    text = STATUS_SKILL.read_text(encoding="utf-8")
    resolved = text.index("Resolved corpus context")
    registry = text.index("Consumer project registry")
    assert resolved < registry
    assert 'workspace_role: "corpus-root"' in text
    assert "Read `config.yaml` from the logical workspace root" in text


def test_headless_status_declares_real_effects():
    text = HEADLESS_STATUS_SKILL.read_text(encoding="utf-8")
    assert "writes the configured result artifact" in text
    assert "git ls-remote" in text
    assert "Never modifies corpus source-of-truth files" in text
    assert "Read-only freshness snapshot" not in text
