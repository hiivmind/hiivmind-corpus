# Upgrade Checklists

## File Component Checklist

**Required files for all corpus types:**

| File | Template | Check |
|------|----------|-------|
| Navigate command | `navigate-command.md.template` | Compare sections |
| Config | `config.yaml.template` | Check schema |
| Project awareness | `project-awareness.md.template` | Exists? |

**Additional for plugins:**

| File | Template | Check |
|------|----------|-------|
| plugin.json | `plugin.json.template` | Structure valid? |
| .gitignore | `gitignore.template` | Has required entries? |
| README.md | `readme.md.template` | Exists? |
| CLAUDE.md | `claude.md.template` | Exists? |

---

## Config Schema Checks

**See:** `lib/corpus/patterns/config-parsing.md` for extraction methods with multiple tool implementations.

Read `data/config.yaml` and verify:

| Field | Added In | Purpose | Check |
|-------|----------|---------|-------|
| `schema_version` | v1 | Version tracking | Must be present |
| `corpus.keywords` | v4 | Per-session routing | Array of routing keywords |

**Keywords check (using yq if available, or fallback):**

Using Claude tools:
```
Read: data/config.yaml
Check for presence of: corpus.keywords
```

Using bash with yq:
```bash
yq '.corpus.keywords' data/config.yaml
```

If missing, suggest adding keywords based on corpus name and domain.

---

## Section Checks for Navigate Skill

Read the current navigate skill and check for these sections:

| Section | Added In | Purpose |
|---------|----------|---------|
| `## Process` | Original | Core navigation steps |
| `## Tiered Index Navigation` | v2 | Large corpus support |
| `## Large Structured Files` | v2 | GREP marker handling |
| `## Making Projects Aware` | v3 | Project awareness injection |
