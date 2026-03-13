# Pattern: Markdown Extraction Pipeline

## Purpose

Extract structured relationship data from markdown files during indexing. This is a cross-cutting capability available to all source types — not specific to Obsidian. Any markdown-based source can opt in via the `extraction:` block in its config.yaml source entry.

## When to Use

- During `build` skill — source-scanner agent includes extraction output in scan report
- During `refresh` skill — compare extraction output between old and new state
- When a source has `extraction:` config with any feature enabled

## Prerequisites

- Source files must be accessible (cloned, cached, or local)
- Filename→path lookup table built for wikilink resolution (see sources/obsidian.md)

---

### Extraction Config

Each source in `config.yaml` can include an `extraction:` block:

```yaml
extraction:
  wikilinks: true        # Parse [[wikilinks]] and [text](path.md) links
  frontmatter: true      # Extract YAML frontmatter key-value pairs
  tags: true             # Extract #hashtags as concept label candidates
  dataview: false         # Parse dataview queries (Obsidian-specific, usually false)
```

**Defaults by source type:**

| Source Type | wikilinks | frontmatter | tags | dataview |
|-------------|-----------|-------------|------|----------|
| obsidian | true | true | true | false |
| git | false | true | true | false |
| local | false | true | true | false |
| web | false | false | false | false |
| llms-txt | false | false | false | false |
| generated-docs | false | true | false | false |
| pdf | false | false | false | false |

Sources without an `extraction:` block use these defaults. Explicitly setting `extraction:` overrides all defaults.

---

### Extract Wikilinks

**Algorithm:**

1. For each `.md` file in the source:
   a. Scan for `[[...]]` patterns (Obsidian wikilinks)
   b. Scan for `[text](relative/path.md)` patterns (standard markdown links to local files)
   c. For each link found:
      - Strip alias suffix: `[[file|alias]]` → `file`
      - Separate anchor: `[[file#heading]]` → file=`file`, anchor=`heading`
      - Resolve to full path using filename→path lookup table
      - If ambiguous (multiple filename matches) → skip with warning
      - If unresolvable → skip (placeholder note or external reference)
   d. Record as edge: `{from_path} → {to_path}` with optional `anchor`

**Using bash:**

```bash
# Extract Obsidian wikilinks
grep -oP '\[\[([^\]]+)\]\]' "$file" | sed 's/\[\[//;s/\]\]//' | while read link; do
  # Strip alias
  link="${link%%|*}"
  # Strip anchor
  anchor=""
  if [[ "$link" == *"#"* ]]; then
    anchor="${link#*#}"
    link="${link%%#*}"
  fi
  echo "wikilink:${link}:${anchor}"
done

# Extract standard markdown links to local files
grep -oP '\[([^\]]+)\]\(([^)]+\.md[^)]*)\)' "$file" | grep -v 'http'
```

---

### Extract Frontmatter

**Algorithm:**

1. Read file content
2. If file starts with `---` on line 1:
   a. Find closing `---`
   b. Parse YAML between delimiters
   c. Record all key-value pairs
   d. Note special keys: `tags` (array), `aliases` (array), `cssclasses` (array)
3. If no frontmatter → skip

**Using bash:**

```bash
# Extract frontmatter block
awk '/^---$/{if(n++)exit;next}n' "$file"
```

**Using Claude tools:**

```
Read: file_path={file} limit=20
# Check if line 1 is "---", parse YAML until next "---"
```

---

### Extract Tags

**Algorithm:**

1. Scan file content (outside of code blocks) for `#tag` patterns
2. Match: `#[a-zA-Z][a-zA-Z0-9_/-]*` (Obsidian tag format)
3. Exclude: headings (`# Heading`), code blocks, URLs with fragments
4. Also extract tags from frontmatter `tags:` array if present
5. Deduplicate and record as list

**Using bash:**

```bash
# Extract inline tags (exclude headings and code blocks)
grep -oP '(?<!\w)#[a-zA-Z][a-zA-Z0-9_/-]*' "$file" | grep -v '^#$' | sort -u
```

---

### Extract Headings

**Algorithm:**

1. Scan for markdown headings: lines starting with `#`, `##`, `###`, etc.
2. Record: heading level, heading text, slugified anchor
3. Anchors follow GitHub/Obsidian convention: lowercase, spaces→hyphens, strip special chars

**Using bash:**

```bash
grep -nP '^#{1,6}\s+' "$file" | while read line; do
  level=$(echo "$line" | grep -oP '^[0-9]+:#{1,6}' | grep -oP '#+' | wc -c)
  text=$(echo "$line" | sed 's/^[0-9]*:#{1,6}\s*//')
  echo "h${level}:${text}"
done
```

---

### Source-Scanner Extraction Output Format

The source-scanner agent appends this to its YAML scan report when extraction is enabled:

```yaml
extraction:
  wikilinks:
    - from: "Dashboard++.md"
      to: "Family/Recipes/Spicy-Sweet Buffalo Popcorn.md"
      anchor: null
    - from: "Dashboard++.md"
      to: "Family/Guests/Guest list.md"
      anchor: null
  tags:
    "project":
      - "Work/Projects/Cloud backup.md"
    "favorite": []
  frontmatter_keys:
    "banner": ["Dashboard++.md", "Family/Recipes/Smores.md"]
    "cssclasses": ["Dashboard++.md"]
  headings:
    "Dashboard++.md":
      - {level: 1, text: "Family", anchor: "family"}
      - {level: 1, text: "Personal Projects", anchor: "personal-projects"}
      - {level: 1, text: "Work", anchor: "work"}
      - {level: 1, text: "Vault Info", anchor: "vault-info"}
  warnings:
    - "Skipped ambiguous wikilink [[README]] — resolves to 2 files"
```

**Merging extraction from multiple sources:** When a corpus has multiple sources, each source-scanner produces its own extraction block. The build skill merges them by prefixing all paths with `{source_id}:` before passing to graph generation.

---

## Related Patterns

- [sources/obsidian.md](sources/obsidian.md) — Primary consumer; enables all extraction features by default
- [sources/git.md](sources/git.md) — Can opt in to frontmatter and tag extraction
- [sources/local.md](sources/local.md) — Can opt in to frontmatter and tag extraction
- [graph.md](graph.md) — Extraction output feeds into graph generation
- [scanning.md](scanning.md) — Extraction extends the source-scanner scan report
