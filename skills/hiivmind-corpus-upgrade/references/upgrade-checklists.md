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

---

## Naming Convention Checks (Plugins Only)

**Applies to:** Corpora with `.claude-plugin/plugin.json`

| Component | Expected Path | Common Violations |
|-----------|---------------|-------------------|
| Navigate command | `commands/navigate.md` | `commands/hiivmind-corpus-{name}.md` |
| Navigate skill directory | `skills/navigate/` | `skills/hiivmind-corpus-{name}/` |
| Navigate skill file | `skills/navigate/SKILL.md` | `skills/navigate.md` (flat file) |

**Detection:**
```bash
# Extract project short name from directory
CORPUS_DIR=$(basename "$PWD")
PROJECT_SHORT=$(echo "$CORPUS_DIR" | sed 's/hiivmind-corpus-//')

# Check for wrong command name
ls commands/hiivmind-corpus-*.md 2>/dev/null && echo "WRONG_COMMAND_NAME"
! ls commands/navigate.md 2>/dev/null && echo "MISSING_COMMAND"

# Check for wrong skill directory name
ls -d skills/hiivmind-corpus-*/ 2>/dev/null && echo "WRONG_SKILL_DIR"

# Check for flat skill file instead of directory structure
ls skills/navigate.md 2>/dev/null && ! ls -d skills/navigate/ 2>/dev/null && echo "WRONG_SKILL_FILE"
```

---

## Navigate Skill Frontmatter Checks

Read the frontmatter from the navigate skill and verify:

| Field | Expected Format | Example |
|-------|-----------------|---------|
| `name` | `hiivmind-corpus-{project}-navigate` | `hiivmind-corpus-htmx-navigate` |
| `description` | Contains "Triggers:" with keyword list | `Triggers: htmx, ajax, hx-get` |
| `context` | `fork` | Runs skill in isolated sub-agent (ADR-007) |
| `agent` | `Explore` | Agent type for forked execution (ADR-007) |
| `allowed-tools` | `Read, Grep, Glob, WebFetch` | Tools available without prompts (ADR-007) |

**Detection (using Claude tools):**
```
Read: skills/navigate/SKILL.md
Parse YAML frontmatter between --- markers
Check name field matches pattern: hiivmind-corpus-{project}-navigate
Check description contains "Triggers:" or "Trigger:"
Check for "context: fork" in frontmatter
Check for "agent: Explore" in frontmatter
Check for "allowed-tools:" in frontmatter
```

**Detection (using bash):**
```bash
# Extract frontmatter name field
NAME=$(grep "^name:" skills/navigate/SKILL.md | head -1 | cut -d: -f2 | tr -d ' ')

# Check name format
echo "$NAME" | grep -qE "^hiivmind-corpus-.*-navigate$" || echo "WRONG_NAME_FORMAT"

# Check for Triggers keyword
grep -qi "triggers:" skills/navigate/SKILL.md || echo "MISSING_TRIGGERS"

# Check for context: fork (ADR-007)
grep -q "^context: fork" skills/navigate/SKILL.md || echo "MISSING_FORK_CONTEXT"

# Check for agent: Explore (ADR-007)
grep -q "^agent: Explore" skills/navigate/SKILL.md || echo "MISSING_AGENT_EXPLORE"

# Check for allowed-tools (ADR-007)
grep -q "^allowed-tools:" skills/navigate/SKILL.md || echo "MISSING_ALLOWED_TOOLS"
```

---

## Navigate Skill Content Quality Checks

Check the content of the navigate skill for quality issues:

| Check | Indicator | Issue |
|-------|-----------|-------|
| Generic worked example | Contains `repo_owner: example` | Template placeholders not customized |
| Generic path format | Contains `local:team-standards` | Default examples not replaced |
| Unfilled template vars | Contains `{{` | Template variables not filled |
| Old format skill | < 200 lines | Needs full template replacement |

**Detection:**
```bash
# Generic worked example
grep -q "repo_owner: example" skills/navigate/SKILL.md && echo "GENERIC_WORKED_EXAMPLE"

# Generic path format examples
grep -q "local:team-standards" skills/navigate/SKILL.md && echo "GENERIC_PATH_EXAMPLES"

# Unfilled template variables
grep -q "{{" skills/navigate/SKILL.md && echo "UNFILLED_PLACEHOLDERS"

# Old format (line count check)
LINE_COUNT=$(wc -l < skills/navigate/SKILL.md)
[ "$LINE_COUNT" -lt 200 ] && echo "OLD_FORMAT_SKILL"
```

**Note:** Old format skills require full regeneration, not patching. The current template is ~273 lines with comprehensive sections.

---

## Config Schema Migration Checks

Check for deprecated config fields that need migration:

| Old Field | New Field | Migration Action |
|-----------|-----------|------------------|
| `corpus.version` | `schema_version` (top-level) | Move and rename |
| `sources[].name` | `sources[].id` | Rename field |
| `sources[].url` | `sources[].repo_url` | Rename field |
| Missing | `corpus.display_name` | Add field |
| Missing | `schema_version: 2` | Add field |

**Detection:**
```bash
# Old corpus.version field
grep -q "corpus:" data/config.yaml && grep -qE "^\s+version:" data/config.yaml && echo "OLD_CORPUS_VERSION"

# Missing top-level schema_version
grep -q "^schema_version:" data/config.yaml || echo "MISSING_SCHEMA_VERSION"

# Old source field names (name instead of id)
grep -qE "^\s+-\s+name:" data/config.yaml && ! grep -qE "^\s+id:" data/config.yaml && echo "OLD_SOURCE_NAME_FIELD"

# Missing display_name
grep -qE "^\s+display_name:" data/config.yaml || echo "MISSING_DISPLAY_NAME"
```
