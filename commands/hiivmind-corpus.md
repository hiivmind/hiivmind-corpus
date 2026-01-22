---
description: Unified entry point for all corpus operations - describe what you need in natural language
argument-hint: Describe your goal (e.g., "index React docs", "refresh my polars corpus", or just a corpus name)
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "TodoWrite", "AskUserQuestion", "Skill", "Task", "WebFetch"]
---

# Corpus Gateway

Unified entry point for all hiivmind-corpus operations.

**User request:** $ARGUMENTS

---

## Tool Detection (at session start)

Detect yq availability once per session:

```bash
command -v yq >/dev/null 2>&1 && yq --version 2>&1 | head -1
```

Set `yaml_tool: yq` if version >= 4, otherwise `yaml_tool: grep`.

---

## If No Arguments, Show Menu First

When `$ARGUMENTS` is empty, immediately show the main menu using AskUserQuestion:

```json
{
  "questions": [{
    "question": "What would you like to do with documentation corpora?",
    "header": "Corpus",
    "multiSelect": false,
    "options": [
      {"label": "Navigate a corpus", "description": "Ask questions about installed documentation"},
      {"label": "Create a new corpus", "description": "Index documentation for a project"},
      {"label": "Manage existing corpus", "description": "Refresh, enhance, or check status"},
      {"label": "List installed corpora", "description": "See what's available"},
      {"label": "Help", "description": "View commands and learn how this works"}
    ]
  }]
}
```

**After selection, route:**
- "Navigate" → Run discovery, show corpus selection, then `/hiivmind-corpus-navigate`
- "Create" → Run `/hiivmind-corpus-init`
- "Manage" → Run discovery, show corpus selection with actions
- "List" → Run `/hiivmind-corpus-discover`
- "Help" → Display quick reference (see Help Actions)

---

## Action Routing

Parse `$ARGUMENTS` to determine intent and route to the appropriate action section.

### Init/Create Actions

**Keywords:** "create", "new", "index", "set up", "scaffold", "initialize", "start corpus"

**Step 1: Confirm target**

If project/library mentioned in arguments, extract it. Otherwise ask:

```json
{
  "questions": [{
    "question": "What project or library would you like to create a corpus for?",
    "header": "Project",
    "multiSelect": false,
    "options": [
      {"label": "Enter GitHub URL", "description": "Provide repository URL like github.com/org/repo"},
      {"label": "Enter project name", "description": "I'll search for the official docs"},
      {"label": "Local documentation", "description": "Index docs in this directory"}
    ]
  }]
}
```

**Step 2: Run skill**

Run `/hiivmind-corpus-init` with detected context.

---

### Add Source Actions

**Keywords:** "add", "include", "import", "fetch", "clone", "source", "extend with", "also index"

**Step 1: Verify corpus exists**

Check for `data/config.yaml` in current directory or ask which corpus to extend.

**Step 2: Identify source type**

If source URL/path mentioned, extract it. Otherwise ask:

```json
{
  "questions": [{
    "question": "What type of source would you like to add?",
    "header": "Source",
    "multiSelect": false,
    "options": [
      {"label": "Git repository", "description": "Clone and index a GitHub/GitLab repo"},
      {"label": "Web pages", "description": "Fetch and cache documentation websites"},
      {"label": "Local files", "description": "Include files already on this machine"},
      {"label": "llms.txt manifest", "description": "Site with llms.txt discovery file"}
    ]
  }]
}
```

**Step 3: Run skill**

Run `/hiivmind-corpus-add-source` with source details.

---

### Build Actions

**Keywords:** "build", "analyze", "scan", "create index", "finish setup", "index now"

**Step 1: Verify corpus structure**

Check for `data/config.yaml` and sources configured.

**Step 2: Run skill**

Run `/hiivmind-corpus-build` to collaboratively create the index.

---

### Navigate Actions

**Keywords:** "navigate", "find", "search", "look up", "what does", "how do", "explain", "show me", "where is"

**Step 1: Discover corpora**

Run `/hiivmind-corpus-discover` internally to find available corpora.

**Step 2: Select corpus (if multiple)**

If only one corpus is built, use it. Otherwise show corpus selection:

```json
{
  "questions": [{
    "question": "Which corpus would you like to query?",
    "header": "Select",
    "multiSelect": false,
    "options": [
      {"label": "polars [built]", "description": "Polars DataFrame documentation"},
      {"label": "ibis [stale]", "description": "Ibis SQL expressions - 3 commits behind"},
      {"label": "react [placeholder]", "description": "Not yet indexed - run build"}
    ]
  }]
}
```

**Step 3: Run skill**

Run `/hiivmind-corpus-navigate` with the query and corpus context.

---

### Refresh Actions

**Keywords:** "update", "refresh", "sync", "check", "upstream", "stale", "status", "is up to date", "current", "behind"

**Step 1: Identify corpus**

If corpus name mentioned, use it. If in corpus directory, use current. Otherwise discover and ask:

```json
{
  "questions": [{
    "question": "Which corpus would you like to refresh?",
    "header": "Refresh",
    "multiSelect": false,
    "options": [
      {"label": "polars", "description": "Last refreshed 3 days ago"},
      {"label": "ibis", "description": "5 commits behind upstream"},
      {"label": "All stale", "description": "Refresh all corpora that need updates"}
    ]
  }]
}
```

**Step 2: Run skill**

Run `/hiivmind-corpus-refresh` with corpus context.

---

### Enhance Actions

**Keywords:** "expand", "deepen", "more detail", "enhance", "elaborate", "deeper coverage", "add depth"

**Step 1: Identify corpus and topic**

If topic mentioned (e.g., "lazy API", "authentication"), extract it. Otherwise ask:

```json
{
  "questions": [{
    "question": "What topic would you like to enhance?",
    "header": "Topic",
    "multiSelect": false,
    "options": [
      {"label": "Specify topic", "description": "Enter the topic or section to expand"},
      {"label": "Review index", "description": "Show current index to choose from"},
      {"label": "Shallow sections", "description": "Find sections that need more depth"}
    ]
  }]
}
```

**Step 2: Run skill**

Run `/hiivmind-corpus-enhance` with topic context.

---

### Upgrade Actions

**Keywords:** "upgrade", "migrate", "latest", "standards", "template", "modernize", "update structure"

**Step 1: Identify corpus**

If corpus name mentioned, use it. If in corpus directory, use current. Otherwise discover and ask.

**Step 2: Run skill**

Run `/hiivmind-corpus-upgrade` to apply latest template standards.

---

### Discover/List Actions

**Keywords:** "list", "show", "available", "installed", "discover", "what corpora", "which corpora"

Run `/hiivmind-corpus-discover` to find and display all installed corpora with status.

---

### Awareness Actions

**Keywords:** "awareness", "configure claude", "setup claude", "capabilities", "tour", "what can", "claude.md", "teach claude"

Run `/hiivmind-corpus-awareness` to add plugin awareness to CLAUDE.md.

---

### Help Actions

**Keywords:** "help", "how", "what", "commands", "?", "usage", "guide"

Display quick reference:

```
═══════════════════════════════════════════════════════════
HIIVMIND-CORPUS - Documentation Corpus Manager
═══════════════════════════════════════════════════════════

CREATE
  /hiivmind-corpus create [project]     Create new corpus
  /hiivmind-corpus add [source]         Add source to existing corpus
  /hiivmind-corpus build                Build/rebuild the index

NAVIGATE
  /hiivmind-corpus                      Interactive menu
  /hiivmind-corpus [question]           Query installed corpora
  /hiivmind-corpus list                 Show installed corpora

MAINTAIN
  /hiivmind-corpus refresh [corpus]     Check/apply upstream updates
  /hiivmind-corpus enhance [topic]      Deepen coverage on topic
  /hiivmind-corpus upgrade [corpus]     Apply latest template standards

CONFIGURE
  /hiivmind-corpus awareness            Add plugin awareness to CLAUDE.md

NATURAL LANGUAGE EXAMPLES
  "index the polars docs"               → init + build
  "add kent's blog to my react corpus"  → add-source
  "is my polars corpus up to date?"     → refresh (status)
  "more detail on lazy evaluation"      → enhance
  "what corpora do I have?"             → discover

═══════════════════════════════════════════════════════════
```

---

## Skill Dispatch

**Single skill:** Run the skill and let it handle the workflow.

| Intent | Skill |
|--------|-------|
| init | `/hiivmind-corpus-init` |
| add-source | `/hiivmind-corpus-add-source` |
| build | `/hiivmind-corpus-build` |
| enhance | `/hiivmind-corpus-enhance` |
| refresh | `/hiivmind-corpus-refresh` |
| upgrade | `/hiivmind-corpus-upgrade` |
| discover | `/hiivmind-corpus-discover` |
| awareness | `/hiivmind-corpus-awareness` |
| navigate | `/hiivmind-corpus-navigate` |

**Before running any skill**, briefly state the context:

```
**Context**: {detected context}
**Intent**: {detected intent}
**Target corpus**: {corpus name if identified}
```

**CRITICAL:** Skills contain all instructions. Do NOT:
- Create directories with mkdir
- Copy patterns from existing corpora
- Generate files without reading templates
- Skip running the skill

---

## Multi-Skill Orchestration

For compound intents, run skills in sequence using TodoWrite to track progress.

| Request | Chain |
|---------|-------|
| "index {project}" | init → build |
| "add {source} and index" | add-source → build |
| "refresh and enhance {topic}" | refresh → enhance |
| "create corpus with multiple sources" | init → add-source → build |

**Execution pattern:**
1. Use TodoWrite to create task list
2. Run first skill: `/hiivmind-corpus-init`
3. When it completes → Run next skill: `/hiivmind-corpus-build`
4. Mark tasks complete as each skill finishes

**IMPORTANT:** Always run each skill - never try to execute skill logic yourself.

---

## Corpus Selection Menu

When user needs to select from installed corpora (for navigate, manage, etc.):

```json
{
  "questions": [{
    "question": "Which corpus would you like to work with?",
    "header": "Select",
    "multiSelect": false,
    "options": [
      {"label": "polars [built]", "description": "Polars DataFrame documentation"},
      {"label": "ibis [stale]", "description": "Ibis SQL expressions - 3 commits behind"},
      {"label": "react [placeholder]", "description": "Not yet indexed - run build"}
    ]
  }]
}
```

**Status indicators:**
- `[built]` - Index has real entries, ready to use
- `[stale]` - Source has updates not in index
- `[placeholder]` - Needs `/hiivmind-corpus-build`

---

## Corpus Action Menu

After selecting a corpus for management:

```json
{
  "questions": [{
    "question": "What would you like to do with polars?",
    "header": "Action",
    "multiSelect": false,
    "options": [
      {"label": "Navigate", "description": "Ask questions about Polars documentation"},
      {"label": "Check freshness", "description": "See if source has updates"},
      {"label": "Enhance", "description": "Add more depth to specific topics"},
      {"label": "Refresh", "description": "Sync index with upstream changes"}
    ]
  }]
}
```

**For placeholder corpora, offer different actions:**

```json
{
  "questions": [{
    "question": "This corpus needs to be built. What would you like to do?",
    "header": "Action",
    "multiSelect": false,
    "options": [
      {"label": "Build now", "description": "Create the index collaboratively"},
      {"label": "Add sources first", "description": "Include additional documentation sources"}
    ]
  }]
}
```

---

## Context Detection

When needed for routing decisions, detect current context:

```bash
# In corpus directory?
test -f data/config.yaml && echo "IN_CORPUS=true"

# In marketplace?
test -f .claude-plugin/marketplace.json && echo "IN_MARKETPLACE=true"

# In project without corpus?
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null && echo "IN_PROJECT=true"
```

**Context + valid operations:**

| Context | Valid Operations |
|---------|------------------|
| In corpus directory | add-source, build, enhance, refresh, upgrade, navigate |
| In marketplace | init (add), batch refresh, batch upgrade |
| In project (no corpus) | init |
| Fresh directory | init |

---

## Error Handling

**No corpora installed:**

```
No documentation corpora are installed yet.

Would you like to:
1. **Create a new corpus** - Index documentation for a project
2. **Install from marketplace** - `/plugin install hiivmind-corpus-polars@hiivmind`

Or describe what you'd like to index: "/hiivmind-corpus index the react docs"
```

**Unrecognized project/library:**

```
I'm not familiar with "{project}". Could you provide:
1. The GitHub repository URL, or
2. The documentation website URL

I'll help set up a corpus from there.
```

**Operation not valid for context:**

```
{operation} isn't available here because {reason}.

Did you mean to:
1. {alternative action 1}
2. {alternative action 2}
```

---

## Example Sessions

### Natural Language: New Corpus

**User:** `/hiivmind-corpus index the polars python library`

**Response:**
```
**Context**: Fresh directory
**Intent**: init → build
**Target**: Polars DataFrame library
```

Then run `/hiivmind-corpus-init` followed by `/hiivmind-corpus-build`.

### Natural Language: Status Check

**User:** `/hiivmind-corpus is my polars corpus up to date?`

**Response:**
```
**Context**: Has installed corpora
**Intent**: refresh (status mode)
**Target**: polars
```

Then run `/hiivmind-corpus-refresh`.

### Natural Language: Enhancement

**User:** `/hiivmind-corpus I need more detail on the lazy API`

**Response:**
```
**Context**: In corpus or has corpora
**Intent**: enhance
**Target**: lazy API section
```

Then run `/hiivmind-corpus-enhance`.

### No Arguments: Interactive

**User:** `/hiivmind-corpus`

Shows main menu with AskUserQuestion, then routes based on selection.
