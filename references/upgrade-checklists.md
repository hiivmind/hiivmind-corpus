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

**Note:** The "Making Projects Aware" section should NOT be in the skill - it belongs in the command's help output.

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

**Note:** The "Making Projects Aware" section should NOT be in the skill - it belongs in the command.

### Navigate Skill Allowed Tools

| Tool | Required | Purpose |
|------|----------|---------|
| `Read` | Yes | Read documentation files |
| `Grep` | Yes | Search indexes and content |
| `Glob` | Yes | Check for local clones |
| `WebFetch` | Yes | Fetch remote content |
| `AskUserQuestion` | Yes | Clarify when no direct match found |

### Navigate Skill Content Quality

| Check | Violation | Detection |
|-------|-----------|-----------|
| No maintenance references | `SKILL_HAS_MAINTENANCE_REFS` | `grep -q "/hiivmind-corpus" skills/navigate/SKILL.md` |
| No project awareness section | `SKILL_HAS_PROJECT_AWARENESS` | `grep -q "Making Projects Aware" skills/navigate/SKILL.md` |
| Has AskUserQuestion tool | `MISSING_ASKUSERQUESTION_TOOL` | `grep -q "AskUserQuestion" skills/navigate/SKILL.md` |

### Navigate Command Sections (commands/navigate.md)

| Section | Required | Description |
|---------|----------|-------------|
| Frontmatter: `description` | Yes | Command description |
| Frontmatter: `argument-hint` | Yes | Example usage |
| Frontmatter: `allowed-tools` | Yes | Should only be `["Skill"]` |
| If No Arguments | Yes | Help message with examples |
| If Arguments Provided | Yes | Invokes the navigate skill |

**Note:** The command should be a thin wrapper (~30-40 lines) that delegates to the skill. Commands > 50 lines likely duplicate skill logic.

### ADR-005 Compliance

| Check | Expected | Command |
|-------|----------|---------|
| Has navigate skill | `skills/navigate/SKILL.md` exists | `ls skills/navigate/SKILL.md` |
| Has navigate command | `commands/navigate.md` exists | `ls commands/navigate.md` |
| Command is thin wrapper | ≤ 50 lines | `wc -l < commands/navigate.md` |
| Skill is pure navigation | No `/hiivmind-corpus` references | `grep -c "/hiivmind-corpus" skills/navigate/SKILL.md` (should be 0) |

### Command/Skill Separation

| Check | Violation | Detection |
|-------|-----------|-----------|
| Command duplicates skill logic | `COMMAND_DUPLICATES_SKILL` | `[ $(wc -l < commands/navigate.md) -gt 50 ]` |
| Skill has maintenance references | `SKILL_HAS_MAINTENANCE_REFS` | `grep -q "/hiivmind-corpus" skills/navigate/SKILL.md` |
| Skill has project awareness section | `SKILL_HAS_PROJECT_AWARENESS` | `grep -q "Making Projects Aware" skills/navigate/SKILL.md` |

**Correct separation:**
- **Command**: User entry point with help, examples, and project awareness mention
- **Skill**: Pure navigation (read indexes, fetch docs, answer questions)

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
    CMD_LINES=$(wc -l < commands/navigate.md)
    if [ "$CMD_LINES" -gt 50 ]; then
      echo "⚠️  Command too long ($CMD_LINES lines > 50) - duplicates skill logic"
    else
      echo "✅ Command is thin wrapper ($CMD_LINES lines)"
    fi
  fi

  if [ -f "skills/navigate/SKILL.md" ]; then
    if grep -q "/hiivmind-corpus" skills/navigate/SKILL.md 2>/dev/null; then
      echo "⚠️  Skill has maintenance references (should be removed)"
    else
      echo "✅ Skill is pure navigation"
    fi

    if grep -q "AskUserQuestion" skills/navigate/SKILL.md 2>/dev/null; then
      echo "✅ Skill has AskUserQuestion tool"
    else
      echo "⚠️  Skill missing AskUserQuestion in allowed-tools"
    fi
  fi
fi

# Config fields
echo ""
echo "=== Config Fields ==="
grep -q "keywords:" data/config.yaml 2>/dev/null && echo "✅ corpus.keywords" || echo "❌ corpus.keywords"
```
