---
name: hiivmind-corpus-awareness
description: >
  Add plugin skill awareness to CLAUDE.md files. Explains what skills this plugin provides,
  when to use each skill, and how to invoke them. Supports user-level (with corpus cache)
  or repo-level injection. Trigger when: "add awareness", "plugin awareness",
  "configure Claude for corpus", "setup CLAUDE.md", "enable corpus features", "capabilities tour".
---

# Plugin Skill Awareness

Configure CLAUDE.md with hiivmind-corpus skill awareness using a What/When/How structure.

## Scope

| Does | Does NOT |
|------|----------|
| Explain what skills this plugin provides | Execute corpus operations |
| Show when to use each skill | Create or modify corpora |
| Describe how to invoke skills | Navigate documentation |
| Edit CLAUDE.md with awareness section | Initialize workspace (use init skill) |
| Cache installed corpora (user-level) | Build corpus indexes |

## Phase Overview

```
1. CONTEXT  -> 2. WHAT      -> 3. WHEN      -> 4. HOW       -> 5. INJECT
   (target)     (skills)       (triggers)     (invoke)       (edit)
      |            |              |              |              |
   Ask where   Present 8     Show trigger   Explain        Preview +
   to inject   skills        mapping        invocation     confirm edit
```

---

## Phase 1: CONTEXT

**Goal:** Determine injection target and check for existing awareness section.

### Step 1: Ask Injection Target

Use AskUserQuestion:

```
Where would you like to add corpus awareness?

Options:
  1. User-level (~/.claude/CLAUDE.md) - Personal corpus collection across all projects
  2. Repo-level ({repo}/CLAUDE.md) - Team projects using specific corpora
  3. Cancel

[Select option]
```

### Step 2: Check Target File

**If user-level selected:**
- Check if `~/.claude/CLAUDE.md` exists
- If not, offer to create it

**If repo-level selected:**
- Check if `CLAUDE.md` exists in current project root
- If not, offer to create it

### Step 3: Check for Existing Section

Search target CLAUDE.md for existing hiivmind-corpus awareness section:
- Look for "## Documentation Corpus" or "hiivmind-corpus"

### STOP Point - No CLAUDE.md

```
No CLAUDE.md found at {target_path}.

Would you like to:
  1. Create CLAUDE.md with plugin awareness section
  2. Cancel

[Select option]
```

### STOP Point - Existing Awareness

If CLAUDE.md already has "hiivmind-corpus" section:

```
CLAUDE.md already has hiivmind-corpus awareness.

Would you like to:
  1. Update/replace existing section
  2. View current section
  3. Cancel

[Select option]
```

---

## Phase 2: WHAT - Plugin Skills

**Goal:** Present what skills this plugin provides.

**See:** `lib/corpus/patterns/capability-awareness.md` (WHAT section)

### Present Skills

```
=== What hiivmind-corpus Provides ===

This plugin has 8 skills for documentation corpus management:

**Primary: Using Corpora**
1. **Navigate**
   Query across all installed corpora from a single entry point.
   Checks cache first for fast lookup.

2. **Discover**
   Find all installed corpora across 4 installation locations.
   Updates cache in ~/.claude/CLAUDE.md.

**Secondary: Maintaining Corpora**
3. **Refresh**
   Sync corpus index with upstream documentation changes.

4. **Enhance**
   Deepen coverage on specific topics in existing index.

5. **Upgrade**
   Update existing corpora to latest template standards.

**Tertiary: Creating Corpora**
6. **Init**
   Create corpus structure for any open-source project.

7. **Build**
   Collaboratively analyze docs and create the index.

8. **Add Source**
   Extend corpus with git repos, local docs, or web pages.

Continue to see when to use each skill? [Yes / Skip to inject]
```

---

## Phase 3: WHEN - Trigger Mapping

**Goal:** Show when each skill should be used.

**See:** `lib/corpus/patterns/capability-awareness.md` (WHEN section)

### Present Trigger Table

```
=== When to Use Each Skill ===

| You Need To... | Use This Skill |
|----------------|----------------|
| Find in indexed documentation | Navigate |
| Look up what X docs say about... | Navigate |
| List all installed corpora | Discover |
| Sync with upstream doc changes | Refresh |
| More detail on specific topic | Enhance |
| Update corpus to latest format | Upgrade |
| Create corpus for new library | Init |
| Build index after init | Build |
| Add another doc source | Add Source |

### Proactive Suggestions

Claude should suggest this plugin when:
- User asks about library functionality (suggest navigate)
- User mentions "docs are outdated" (suggest refresh)
- User adds new library/dependency (suggest init)
- User wants more detail on indexed topic (suggest enhance)

Continue to see how to invoke? [Yes / Skip to inject]
```

---

## Phase 4: HOW - Invocation Methods

**Goal:** Explain how to invoke the plugin.

**See:** `lib/corpus/patterns/capability-awareness.md` (HOW section)

### Present Invocation Options

```
=== How to Invoke ===

### Gateway Command (Recommended)

/hiivmind-corpus [describe what you want]

The gateway auto-detects intent and routes to the appropriate skill.

Examples:
  /hiivmind-corpus what does Polars say about lazy evaluation
  /hiivmind-corpus list my corpora
  /hiivmind-corpus refresh my React docs
  /hiivmind-corpus create corpus for FastAPI

### Direct Skill Invocation

When you know exactly which skill:
  Skill: hiivmind-corpus-navigate
  Skill: hiivmind-corpus-discover
  Skill: hiivmind-corpus-init

### Interactive Menu

/hiivmind-corpus (no arguments) → shows numbered menu

Continue to inject into CLAUDE.md? [Yes / Cancel]
```

---

## Phase 5: INJECT

**Goal:** Generate awareness section and edit CLAUDE.md.

**See:** `lib/corpus/patterns/capability-awareness.md` (Templates section)

### Step 1: Generate Section

**If user-level injection:**

1. Run discover skill to find all installed corpora
2. Build cache table with corpus names, keywords, locations
3. Generate user-level template with cache

**If repo-level injection:**

1. Ask which corpora are relevant to this project
2. Generate repo-level template with specific corpora

### Step 2: Preview

```
=== CLAUDE.md Addition Preview ===

[Show generated section]

Insert location: End of file / After [section name]

Options:
  1. Add to CLAUDE.md
  2. Choose different location
  3. Cancel

[Select option]
```

### Step 3: Execute Edit

Use Edit tool to:
- Append to CLAUDE.md (if appending)
- Insert after specified section (if location chosen)
- Replace existing section (if updating)

### STOP Point - Success

```
CLAUDE.md updated successfully!

Added hiivmind-corpus skill awareness section.
{If user-level: "Cache contains N installed corpora."}

Next steps:
  1. Try a documentation query (/hiivmind-corpus what does X say about...)
  2. List installed corpora (/hiivmind-corpus list my corpora)
  3. Done

[Select option]
```

---

## Quick Reference

### Add Awareness

```
/hiivmind-corpus add awareness
/hiivmind-corpus configure Claude for corpus
/hiivmind-corpus what can you do
```

---

## Related Skills

- **hiivmind-corpus-discover** - Updates corpus cache in CLAUDE.md
- **hiivmind-corpus-navigate** - Uses cache for fast corpus lookup
- **hiivmind-corpus-init** - Initialize new corpus after adding awareness

## Pattern Library

| Pattern | Purpose |
|---------|---------|
| `lib/corpus/patterns/capability-awareness.md` | Skill registry, trigger mapping, CLAUDE.md templates |
