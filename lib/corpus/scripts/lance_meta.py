#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["lancedb>=0.20.0", "pyarrow>=15.0.0"]
# ///
"""Print the _meta table of a Lance embeddings dir as a flat JSON object.

The _meta table is a key/value table (columns `key`, `value`); this script
reshapes it into a single JSON object, e.g.
  {"model": "...", "dimensions": "384", "generated_at": "...", "entry_count": "747"}
Values are stored as strings by embed.py and passed through as-is.

Usage: lance_meta.py <lance_dir>
Exit codes: 0 ok, 1 usage/open error, 2 no _meta table.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import META_TABLE


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: lance_meta.py <lance_dir>", file=sys.stderr)
        return 1
    import lancedb

    try:
        db = lancedb.connect(sys.argv[1])
        names = db.table_names()
    except Exception as exc:  # unreadable / not a lance dir
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if META_TABLE not in names:
        print("error: no _meta table", file=sys.stderr)
        return 2

    arrow = db.open_table(META_TABLE).to_arrow()
    keys = arrow.column("key").to_pylist()
    values = arrow.column("value").to_pylist()
    print(json.dumps(dict(zip(keys, values))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
