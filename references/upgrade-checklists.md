# Upgrade Checklists

Complete checklists for verifying corpus compliance with current hiivmind-corpus standards.

## User-level / Repo-local Skills

Simpler structure without plugin manifest.

### Required Files

| File | Purpose | Check |
|------|---------|-------|
| `SKILL.md` | Navigate skill (from `navigate-skill.md.template`) | `ls SKILL.md` |
| `data/config.yaml` | Corpus configuration | `ls data/config.yaml` |
| `data/index.md` | Documentation index | `ls data/index.md` |
| `references/project-awareness.md` | Injection snippet | `ls references/project-awareness.md` |

### Config Schema Fields

| Field | Required | Check |
|-------|----------|-------|
| `corpus.name` | Yes | `grep "name:" data/config.yaml` |
| `corpus.display_name` | Yes | `grep "display_name:" data/config.yaml` |
| `corpus.keywords` | Yes | `grep "keywords:" data/config.yaml` |
| `sources[]` | Yes | `grep "sources:" data/config.yaml` |

### SKILL.md Sections

| Section | Required | Description |
|---------|----------|-------------|
| Frontmatter with `name`, `description` | Yes | Trigger keywords in description |
| Navigation Process | Yes | How to find and access content |
| Index Search | Yes | Searching index for relevant entries |
| Source Access | Yes | Per-source-type access patterns |
| File Locations | Yes | Where files are stored |
| Output | Yes | How to format responses |
| Making Projects Aware | Recommended | Reference to project-awareness.md |
| Corpus Maintenance | Recommended | Points to parent skills |

---

## Standalone Plugin / Marketplace Plugin

Full plugin structure with manifest and dual navigate implementation.

### Required Files

| File | Purpose | Check |
|------|---------|-------|
| `.claude-plugin/plugin.json` | Plugin manifest | `ls .claude-plugin/plugin.json` |
| `skills/navigate/SKILL.md` | Navigate skill (auto-trigger) | `ls skills/navigate/SKILL.md` |
| `commands/navigate.md` | Navigate command (explicit) | `ls commands/navigate.md` |
| `data/config.yaml` | Corpus configuration | `ls data/config.yaml` |
| `data/index.md` | Documentation index | `ls data/index.md` |
| `references/project-awareness.md` | Injection snippet | `ls references/project-awareness.md` |
| `.gitignore` | Ignore .source/ and .cache/ | `ls .gitignore` |
| `README.md` | Plugin documentation | `ls README.md` |

### Additional Files (Recommended)

| File | Purpose | Check |
|------|---------|-------|
| `CLAUDE.md` | Plugin self-awareness | `ls CLAUDE.md` |
| `LICENSE` | License file | `ls LICENSE` |

### Config Schema Fields

Same as user-level/repo-local, plus:

| Field | Required | Check |
|-------|----------|-------|
| `corpus.name` | Yes | Core identifier |
| `corpus.display_name` | Yes | Human-readable name |
| `corpus.keywords` | Yes | For skill auto-triggering |
| `sources[].id` | Yes | Source identifier |
| `sources[].type` | Yes | git, local, or web |
| `sources[].last_indexed_sha` | For git sources | Tracks indexed commit |

### Navigate Skill Sections (skills/navigate/SKILL.md)

| Section | Required | Description |
|---------|----------|-------------|
| Frontmatter: `name` | Yes | `{plugin_name}-navigate` |
| Frontmatter: `description` | Yes | Trigger keywords for auto-invocation |
| Navigation Process | Yes | How to find and access content |
| Index Search | Yes | Searching index for relevant entries |
| Path Format | Yes | `{source_id}:{relative_path}` |
| Source Access | Yes | Per-source-type access patterns |
| File Locations | Yes | Where files are stored |
| Output | Yes | How to format responses |
| Making Projects Aware | Recommended | Reference to project-awareness.md |
| Corpus Maintenance | Recommended | Points to parent gateway |

### Navigate Command Sections (commands/navigate.md)

| Section | Required | Description |
|---------|----------|-------------|
| Frontmatter: `description` | Yes | Command description |
| Frontmatter: `argument-hint` | Yes | Example usage |
| Frontmatter: `allowed-tools` | Yes | Tools the command can use |
| If No Arguments | Yes | Help message with examples |
| Navigation Process | Yes | Same as skill |
| Corpus Maintenance | Recommended | Points to parent gateway |

### ADR-005 Compliance

| Check | Expected | Command |
|-------|----------|---------|
| Has navigate skill | `skills/navigate/SKILL.md` exists | `ls skills/navigate/SKILL.md` |
| Has navigate command | `commands/navigate.md` exists | `ls commands/navigate.md` |
| No routing in command | No `hiivmind-corpus-refresh` references | `grep -c "hiivmind-corpus-refresh" commands/navigate.md` (should be 0) |
| Points to parent | Maintenance section references `/hiivmind-corpus` | `grep "/hiivmind-corpus" commands/navigate.md` |

---

## Marketplace Container

The parent marketplace that contains multiple corpus plugins.

### Required Files

| File | Purpose | Check |
|------|---------|-------|
| `.claude-plugin/plugin.json` | Marketplace manifest | `ls .claude-plugin/plugin.json` |
| `.claude-plugin/marketplace.json` | Plugin listing | `ls .claude-plugin/marketplace.json` |
| `CLAUDE.md` | Marketplace self-awareness | `ls CLAUDE.md` |
| `README.md` | Marketplace documentation | `ls README.md` |

### marketplace.json Schema

```json
{
  "name": "marketplace-name",
  "description": "Marketplace description",
  "plugins": [
    {
      "source": "./hiivmind-corpus-{name}",
      "name": "hiivmind-corpus-{name}",
      "description": "Plugin description",
      "version": "1.0.0"
    }
  ]
}
```

### Per-Plugin Verification

For each plugin in the marketplace, run the Standalone Plugin checklist above.

---

## Quick Compliance Check Script

```bash
# Run from corpus root
echo "=== Corpus Compliance Check ==="

# Detect type
if [ -f "SKILL.md" ] && [ -d "data" ]; then
  echo "Type: User-level or Repo-local skill"
  TYPE="skill"
elif [ -f ".claude-plugin/plugin.json" ]; then
  echo "Type: Standalone or Marketplace plugin"
  TYPE="plugin"
else
  echo "Type: Unknown"
  TYPE="unknown"
fi

# Check common requirements
echo ""
echo "=== Required Files ==="
[ -f "data/config.yaml" ] && echo "✅ data/config.yaml" || echo "❌ data/config.yaml"
[ -f "data/index.md" ] && echo "✅ data/index.md" || echo "❌ data/index.md"
[ -f "references/project-awareness.md" ] && echo "✅ references/project-awareness.md" || echo "❌ references/project-awareness.md"

# Plugin-specific checks
if [ "$TYPE" = "plugin" ]; then
  echo ""
  echo "=== ADR-005 Compliance ==="
  [ -f "skills/navigate/SKILL.md" ] && echo "✅ skills/navigate/SKILL.md" || echo "❌ skills/navigate/SKILL.md"
  [ -f "commands/navigate.md" ] && echo "✅ commands/navigate.md" || echo "❌ commands/navigate.md"

  if [ -f "commands/navigate.md" ]; then
    if grep -q "hiivmind-corpus-refresh" commands/navigate.md 2>/dev/null; then
      echo "⚠️  Command has routing table (needs simplification)"
    else
      echo "✅ Command has no routing table"
    fi
  fi
fi

# Config fields
echo ""
echo "=== Config Fields ==="
grep -q "keywords:" data/config.yaml 2>/dev/null && echo "✅ corpus.keywords" || echo "❌ corpus.keywords"
```
