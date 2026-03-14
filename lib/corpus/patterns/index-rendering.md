# Pattern: Deterministic index.md Rendering

## Purpose

Render `index.md` mechanically from `index.yaml`. No LLM involvement. Same input always produces the same output. index.md is a build artifact — never hand-edited, never LLM-interpreted at render time.

## When to Use

- End of `hiivmind-corpus build`
- End of `hiivmind-corpus refresh`
- End of CI refresh workflow
- Any time `index.yaml` is modified

## Prerequisites

- `index.yaml` exists in the corpus root
- `config.yaml` exists in the same directory (provides corpus name and source count)
- `yq` 4.0+ (mikefarah/yq)
- `render-index.sh` present at corpus root (copied from `templates/render-index.sh` during build)

## Rendering Algorithm

**Input:** `index.yaml`
**Output:** `index.md`

**Rules:**

1. **Header:** corpus name, source count, entry count, generation timestamp, "Generated from `index.yaml` — do not edit directly" banner
2. Entries grouped by `category` field (h2 headings), categories sorted **alphabetically**
3. Within each category, entries sorted **alphabetically by `title`**
4. Entry line format: `- **{title}** \`{id}\` - {summary}`
5. Large files (`size: large`): append ` ⚡ GREP - \`{grep_hint}\`` to entry line
6. Stale entries (`stale: true`): append ` ⏳ STALE` marker
7. **Footer:** generation timestamp, "Rendered from index.yaml"

**Idempotency guarantee:** Same `index.yaml` → same `index.md`, every run, regardless of which agent or workflow executes it.

## Implementation

```bash
bash render-index.sh index.yaml
```

The script reads `config.yaml` from the same directory for corpus name and source count. It writes `index.md` in place.

## Example Output

```markdown
# Polars Documentation Index

> Sources: 1 | Entries: 119 | Generated: 2026-03-13T10:00:00Z
> Generated from `index.yaml` — do not edit directly

---

## API

- **API Reference** `polars:api/reference.md` - Complete API reference ⚡ GREP - `grep -n "^## " FILE`

## Guide

- **Getting Started** `polars:user-guide/getting-started.md` - Installation, first DataFrame, basic queries

## Reference

- **Basic Operations** `polars:user-guide/expressions/basic-operations.md` - Arithmetic, comparisons, Boolean operations, counting unique values
- **Data Types** `polars:user-guide/expressions/data-types.md` - Type system, casting, temporal types ⏳ STALE

---

*Rendered from index.yaml at 2026-03-13T10:00:00Z*
```

## Related Patterns

- `index-format-v2.md` — `index.yaml` strict schema and field definitions
- `freshness.md` — SHA-gated freshness checks and stale flagging that produce the `stale: true` entries rendered here
