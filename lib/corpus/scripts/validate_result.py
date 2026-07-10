#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate a headless result file against the corpus result contract.

Usage: validate_result.py <result.yaml> --kind refresh|enrich|migrate|status|graph-validate

See lib/corpus/patterns/headless-contract.md for the schemas.

Exit codes:
  0 - valid
  1 - invalid (errors on stderr, one per line)
  2 - file missing or unparseable
"""
import argparse
import sys
from pathlib import Path

SUPPORTED_VERSIONS = {1}
SOURCE_STATUSES = {"current", "updated", "failed", "skipped-manual"}
REFRESH_EMBEDDINGS = {"updated", "skipped", "no-model", "not-installed", "deferred"}
ENRICH_EMBEDDINGS = {"updated", "skipped", "no-model", "not-installed"}
MIGRATE_STRATEGIES = {"tiered", "single"}
MIGRATE_SKIP_REASONS = {"file-missing", "clone-failed"}
INDEX_FORMATS = {"v2", "v1", "none"}
STATUS_FRESHNESS = {"current", "behind", "unknown"}
GRAPH_SEVERITIES = {"error", "warning"}


def _require_int_or_null(data, key, errors, ctx=""):
    """Key must be present; value may be int or None."""
    label = f"{ctx}{key}"
    if key not in data:
        _err(errors, f"missing required key: {label}")
        return
    if data[key] is not None and not isinstance(data[key], int):
        _err(errors, f"wrong type for {label}: expected int or null, got {type(data[key]).__name__}")


def _err(errors, msg):
    errors.append(msg)


def _require(data, key, types, errors, ctx=""):
    label = f"{ctx}{key}"
    if key not in data:
        _err(errors, f"missing required key: {label}")
        return None
    if not isinstance(data[key], types):
        _err(errors, f"wrong type for {label}: expected {types}, got {type(data[key]).__name__}")
        return None
    return data[key]


def validate(data: dict, kind: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["result is not a mapping"]

    version = _require(data, "contract_version", int, errors)
    if version is not None and version not in SUPPORTED_VERSIONS:
        _err(errors, f"unsupported contract_version: {version}")

    got_kind = _require(data, "kind", str, errors)
    if got_kind is not None and got_kind != kind:
        _err(errors, f"kind mismatch: expected {kind}, got {got_kind}")

    _require(data, "corpus", str, errors)
    _require(data, "run_at", str, errors)
    _require(data, "errors", list, errors)

    if kind == "refresh":
        sources = _require(data, "sources", list, errors)
        for i, s in enumerate(sources or []):
            if not isinstance(s, dict):
                _err(errors, f"sources[{i}] is not a mapping")
                continue
            _require(s, "id", str, errors, ctx=f"sources[{i}].")
            _require(s, "type", str, errors, ctx=f"sources[{i}].")
            status = _require(s, "status", str, errors, ctx=f"sources[{i}].")
            if status is not None and status not in SOURCE_STATUSES:
                _err(errors, f"sources[{i}].status invalid: {status}")
        ic = _require(data, "index_changes", dict, errors)
        if ic is not None:
            for k in ("added", "modified", "removed"):
                _require(ic, k, int, errors, ctx="index_changes.")
            _require(ic, "stale_entries", list, errors, ctx="index_changes.")
        emb = _require(data, "embeddings", str, errors)
        if emb is not None and emb not in REFRESH_EMBEDDINGS:
            _err(errors, f"embeddings invalid: {emb}")
        if "embeddings_lag" in data and data["embeddings_lag"] is not None \
                and not isinstance(data["embeddings_lag"], int):
            _err(errors, "wrong type for embeddings_lag: expected int or null")

    elif kind == "enrich":
        for k in ("enriched", "skipped", "concepts_assigned"):
            _require(data, k, int, errors)
        _require(data, "new_concept_candidates", list, errors)
        ver = _require(data, "verification", dict, errors)
        if ver is not None:
            _require(ver, "sampled", int, errors, ctx="verification.")
            _require(ver, "failed", int, errors, ctx="verification.")
            _require(ver, "drift_entries", list, errors, ctx="verification.")
        emb = _require(data, "embeddings", str, errors)
        if emb is not None and emb not in ENRICH_EMBEDDINGS:
            _err(errors, f"embeddings invalid: {emb}")

    elif kind == "migrate":
        _require(data, "entries_migrated", int, errors)
        skipped = _require(data, "entries_skipped", list, errors)
        for i, s in enumerate(skipped or []):
            if not isinstance(s, dict):
                _err(errors, f"entries_skipped[{i}] is not a mapping")
                continue
            _require(s, "id", str, errors, ctx=f"entries_skipped[{i}].")
            reason = _require(s, "reason", str, errors, ctx=f"entries_skipped[{i}].")
            if reason is not None and reason not in MIGRATE_SKIP_REASONS:
                _err(errors, f"entries_skipped[{i}].reason invalid: {reason}")
        sections = _require(data, "sections", list, errors)
        for i, sec in enumerate(sections or []):
            if not isinstance(sec, str):
                _err(errors, f"sections[{i}] is not a string")
        strategy = _require(data, "strategy", str, errors)
        if strategy is not None and strategy not in MIGRATE_STRATEGIES:
            _err(errors, f"strategy invalid: {strategy}")
        _require(data, "id_parity", bool, errors)
        emb = _require(data, "embeddings", str, errors)
        if emb is not None and emb != "skipped":
            _err(errors, f"embeddings must be 'skipped' for migrate, got: {emb}")

    elif kind == "status":
        fmt = _require(data, "index_format", str, errors)
        if fmt is not None and fmt not in INDEX_FORMATS:
            _err(errors, f"index_format invalid: {fmt}")
        sources = _require(data, "sources", list, errors)
        for i, s in enumerate(sources or []):
            if not isinstance(s, dict):
                _err(errors, f"sources[{i}] is not a mapping")
                continue
            _require(s, "id", str, errors, ctx=f"sources[{i}].")
            _require(s, "type", str, errors, ctx=f"sources[{i}].")
            fresh = _require(s, "freshness", str, errors, ctx=f"sources[{i}].")
            if fresh is not None and fresh not in STATUS_FRESHNESS:
                _err(errors, f"sources[{i}].freshness invalid: {fresh}")
        _require(data, "stale_entries", int, errors)
        _require_int_or_null(data, "embeddings_lag", errors)
        _require(data, "refresh_needed", bool, errors)

    elif kind == "graph-validate":
        _require(data, "concepts", int, errors)
        _require(data, "relationships", int, errors)
        issues = _require(data, "issues", list, errors)
        for i, iss in enumerate(issues or []):
            if not isinstance(iss, dict):
                _err(errors, f"issues[{i}] is not a mapping")
                continue
            sev = _require(iss, "severity", str, errors, ctx=f"issues[{i}].")
            if sev is not None and sev not in GRAPH_SEVERITIES:
                _err(errors, f"issues[{i}].severity invalid: {sev}")
            _require(iss, "rule", str, errors, ctx=f"issues[{i}].")
            _require(iss, "detail", str, errors, ctx=f"issues[{i}].")
        _require(data, "valid", bool, errors)

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate a headless result file")
    parser.add_argument("file", help="Path to result YAML file")
    parser.add_argument("--kind", required=True,
                        choices=["refresh", "enrich", "migrate", "status", "graph-validate"])
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(2)

    import yaml
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        print(f"error: unparseable YAML: {e}", file=sys.stderr)
        sys.exit(2)

    errors = validate(data, args.kind)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
