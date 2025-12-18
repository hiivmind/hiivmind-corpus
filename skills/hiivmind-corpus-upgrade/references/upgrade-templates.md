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
