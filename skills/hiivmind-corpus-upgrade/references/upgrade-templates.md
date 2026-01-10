# Upgrade Report and Section Templates

## Report Template

Present a clear report to the user:

```
Corpus: hiivmind-corpus-polars
Type: Standalone plugin
Location: /path/to/corpus

Upgrade Report:
═══════════════

✅ UP TO DATE:
  - data/config.yaml (schema_version 2)
  - skills/navigate/SKILL.md has Process section
  - .gitignore present

⚠️  MISSING FILES:
  - references/project-awareness.md

⚠️  MISSING CONFIG FIELDS:
  - corpus.keywords (for per-session routing)
    Suggested: polars, dataframe, lazy, expression

⚠️  MISSING SECTIONS in navigate skill:
  - "Tiered Index Navigation" section
  - "Large Structured Files" section
  - "Making Projects Aware" section

Would you like to apply these upgrades?
```

---

## Missing Navigate Skill Sections

### Tiered Index Navigation Section

Append this if missing:

```markdown
## Tiered Index Navigation

Large corpora may use **tiered indexes** with a main index linking to detailed sub-indexes:

\`\`\`
data/
├── index.md              # Main index with section summaries
├── index-reference.md    # Detailed: Reference docs
├── index-guides.md       # Detailed: Guides/tutorials
\`\`\`

**How to navigate:**

1. **Start with main index** (`data/index.md`)
2. **Identify the relevant section** from user's question
3. **If section links to sub-index** (e.g., `→ See [index-actions.md](index-actions.md)`):
   - Read that sub-index for detailed entries
   - The sub-index has the actual file paths
4. **Quick Reference entries** in main index have direct paths - use those for common lookups
```

---

### Large Structured Files Section

Append this if missing:

```markdown
## Large Structured Files

For files marked with `⚡ GREP` in the index, use Grep instead of Read:

\`\`\`bash
# Find a type/definition
grep -n "^type {Name}" file -A 30

# Find references
grep -n "{keyword}" file
\`\`\`

**When to use Grep vs Read:**
- File > 1000 lines → prefer Grep
- Looking for specific definition → Grep with `-A` context
- Need surrounding context → Grep with `-B` and `-A`
```

---

### Making Projects Aware Section

Append this if missing:

```markdown
## Making Projects Aware of This Corpus

If you're working in a project that uses {Project} but doesn't know about this corpus, you can add awareness to the project's CLAUDE.md.

**The `references/project-awareness.md` file** contains a ready-to-use snippet that can be added to any project's CLAUDE.md to make Claude aware of this corpus when working in that project.

### How to Inject

1. Read `references/project-awareness.md` from this corpus
2. Add its contents to the target project's CLAUDE.md (create if needed)
3. The project will now know to use this corpus for {Project} questions

### When to Suggest Injection

Suggest adding project awareness when:
- User is working in a project that heavily uses {Project}
- User repeatedly asks {Project} questions without invoking the corpus
- User says "I keep forgetting to use the docs"
```

---

## Naming Convention Fixes

### Rename Command File

**Issue:** `commands/hiivmind-corpus-{name}.md` exists instead of `commands/navigate.md`

**Fix:**
```bash
OLD_CMD=$(ls commands/hiivmind-corpus-*.md 2>/dev/null | head -1)
if [ -n "$OLD_CMD" ]; then
    git mv "$OLD_CMD" commands/navigate.md
fi
```

### Rename Skill Directory

**Issue:** `skills/hiivmind-corpus-{name}/` exists instead of `skills/navigate/`

**Fix:**
```bash
OLD_DIR=$(ls -d skills/hiivmind-corpus-*/ 2>/dev/null | head -1)
if [ -n "$OLD_DIR" ]; then
    git mv "$OLD_DIR" skills/navigate/
fi
```

### Convert Flat Skill to Directory Structure

**Issue:** `skills/navigate.md` exists as a file instead of `skills/navigate/SKILL.md`

**Fix:**
```bash
if [ -f skills/navigate.md ] && [ ! -d skills/navigate ]; then
    mkdir -p skills/navigate
    git mv skills/navigate.md skills/navigate/SKILL.md
fi
```

---

## Navigate Skill Regeneration

When a navigate skill is flagged as OLD_FORMAT or has GENERIC_WORKED_EXAMPLE issues, it needs full regeneration rather than patching.

### When to Regenerate

Regenerate the entire SKILL.md when:
- Line count < 200 (old format)
- Contains `repo_owner: example` (generic content)
- Missing major sections (Tiered Index Navigation, Large Structured Files, Making Projects Aware)

### Regeneration Process

1. **Read config.yaml** to extract project metadata:
   ```yaml
   # Extract these values:
   corpus.name → for skill name
   corpus.display_name → for title
   sources[0].id → for worked example source_id
   sources[0].type → determines worked example pattern
   sources[0].repo_owner, repo_name, branch, docs_root → for git sources
   sources[0].base_url → for web sources
   ```

2. **Load the template** from hiivmind-corpus:
   - Template: `templates/navigate-skill.md.template`
   - Expected location: `~/.claude/plugins/hiivmind-corpus/templates/` or development path

3. **Fill placeholders** with project-specific values:
   | Placeholder | Source |
   |-------------|--------|
   | `{{plugin_name}}` | `hiivmind-corpus-{corpus.name}` |
   | `{{project_name}}` | `corpus.name` |
   | `{{project_display_name}}` | `corpus.display_name` |
   | `{{source_id}}` | `sources[0].id` |
   | `{{example_path}}` | Generate from first index entry |
   | Worked Example section | Generate based on source type |

4. **Source-specific Worked Examples:**

   **For git sources:**
   ```markdown
   ### Worked Example (IMPORTANT - Follow This Pattern!)

   **Index entry found:** `{source_id}:{example_path}`

   **Step 1 - Parse the path:**
   - `source_id` = `{source_id}` (everything before the colon)
   - `relative_path` = `{example_path}` (everything after the colon)

   **Step 2 - Look up source in config.yaml:**
   ```yaml
   sources:
     - id: {source_id}
       type: git
       repo_owner: {repo_owner}
       repo_name: {repo_name}
       branch: {branch}
       docs_root: {docs_root}
   ```

   **Step 3 - Construct the full path:**
   - Local clone: `.source/{source_id}/{docs_root}/{example_path}`
   - GitHub URL: `https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{docs_root}/{example_path}`
   ```

   **For web sources:**
   ```markdown
   ### Worked Example (IMPORTANT - Follow This Pattern!)

   **Index entry found:** `{source_id}:{cached_file}`

   **Step 1 - Parse the path:**
   - `source_id` = `{source_id}` (everything before the colon)
   - `relative_path` = `{cached_file}` (everything after the colon)

   **Step 2 - Look up source in config.yaml:**
   ```yaml
   sources:
     - id: {source_id}
       type: web
       description: "{description}"
       urls:
         - url: "{original_url}"
           cached_file: "{cached_file}"
   ```

   **Step 3 - Read from cache:**
   - Cache path: `.cache/web/{source_id}/{cached_file}`
   ```

5. **Write the regenerated SKILL.md** to `skills/navigate/SKILL.md`

---

## Enhanced Report Template

Present a clear report with all validation categories:

```
Corpus: hiivmind-corpus-{name}
Type: {Standalone plugin | Marketplace plugin | User-level | Repo-local}
Location: {path}

Upgrade Report:
═══════════════

✅ UP TO DATE:
  - data/config.yaml exists
  - .gitignore present

⚠️  NAMING VIOLATIONS:
  - commands/hiivmind-corpus-airtable.md → should be commands/navigate.md
  - skills/hiivmind-corpus-airtable/ → should be skills/navigate/

⚠️  FRONTMATTER ISSUES:
  - name: "navigate" → should be "hiivmind-corpus-airtable-navigate"
  - description: Missing "Triggers:" keyword list

⚠️  CONTENT QUALITY:
  - Navigate skill uses old format (59 lines vs expected ~270)
  - Worked Example contains generic "repo_owner: example"
  - Path Format contains generic "local:team-standards"

⚠️  CONFIG SCHEMA:
  - Missing schema_version (top-level)
  - Missing corpus.display_name
  - Found deprecated corpus.version field

⚠️  MISSING FILES:
  - references/project-awareness.md

⚠️  MISSING SECTIONS:
  - "Making Projects Aware" section

Would you like to apply these upgrades?
```

---

## Completion Report Template

After applying upgrades, show:

```
Upgrade Complete!
════════════════

Files added:
  - references/project-awareness.md

Files modified:
  - skills/navigate/SKILL.md (+45 lines)

Remember to commit:
  git add -A && git commit -m "Upgrade corpus to latest standards"
```
