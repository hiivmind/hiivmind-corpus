---
name: hiivmind-corpus
description: >
  Unified entry point for managing documentation corpora. Routes requests to:
  init, add-source, build, navigate, refresh, enhance, discover, register, status.
arguments:
  - name: request
    description: What you want to do (optional - shows menu if omitted)
    required: false
---

# hiivmind-corpus Gateway

Route natural language requests to corpus management skills. This is a **router** —
it detects intent and immediately dispatches to the matched skill.

## Dispatch Protocol

**CRITICAL:** This gateway is a ROUTER, not an executor.

1. **DO NOT answer the user's request yourself** — your job is routing
2. **DO NOT pre-validate or gather information** — let the skill handle its own context
3. **Detect intent** from the user's input using the routing table below
4. **IMMEDIATELY invoke the matched skill** using the Skill tool
5. **Let the skill take over** — it will load its own SKILL.md and execute

---

## Routing Table

Match the user's input against these keywords to determine the target skill.
If multiple skills match, prefer the one with the most specific keyword match.

| Skill | Keywords | Example Input |
|-------|----------|---------------|
| `hiivmind-corpus-init` | create, new, set up, scaffold, initialize, start corpus | "create react docs" |
| `hiivmind-corpus-add-source` | add source, include, import, extend with, add docs | "add source from github" |
| `hiivmind-corpus-build` | build, analyze, scan, create index, finish setup, index now | "build my corpus" |
| `hiivmind-corpus-navigate` | navigate, query, ask, search docs, find in docs, documentation for | "polars lazy evaluation" |
| `hiivmind-corpus-refresh` | update, refresh, sync, stale, behind, upstream, is up to date | "refresh polars" |
| `hiivmind-corpus-enhance` | expand, deepen, more detail, enhance, elaborate, deeper coverage | "enhance authentication topic" |
| `hiivmind-corpus-discover` | list, available, installed, discover, what/which/show corpora | "list available corpora" |
| `hiivmind-corpus-register` | register, add corpus, connect corpus, enable corpus, add to registry | "register polars corpus" |
| `hiivmind-corpus-status` | status, health, check, diagnose, info | "check corpus health" |
| `hiivmind-corpus-graph` | graph, show graph, validate graph, concepts, relationships | "show graph" |
| `hiivmind-corpus-bridge` | bridge, cross-corpus, link corpora, registry graph, alias | "bridge polars and clickhouse" |

### Disambiguation

If no clear match, or if multiple skills match equally, present the interactive menu (see below).

### Query fallback

If the input doesn't match any action keyword but contains what looks like a documentation
question (e.g., "polars lazy evaluation", "how do I deploy to fly.io"), route to
`hiivmind-corpus-navigate`.

---

## Interactive Menu (no input)

If invoked with no arguments or no keywords matched, present:

```
What would you like to do?

1. Navigate documentation — Search and query corpus content
2. Create a corpus — Initialize a new documentation corpus
3. Add a source — Add documentation source to existing corpus
4. Build index — Analyze sources and generate index
5. Refresh — Check for upstream changes and update
6. Enhance — Deepen coverage on specific topics
7. Discover — List available corpora
8. Register — Connect a corpus to this project
9. Status — Check corpus health and freshness
```

Route to the selected skill.

---

## Skill Invocation

When dispatching, pass the user's original arguments (minus the routing keywords) to the skill:

```
Skill(
  skill: "hiivmind-corpus-{matched_skill}",
  args: "{remaining_arguments}"
)
```

**Examples:**

| User Input | Matched Skill | Args Passed |
|------------|---------------|-------------|
| `/hiivmind-corpus create react docs` | hiivmind-corpus-init | "react docs" |
| `/hiivmind-corpus polars lazy evaluation` | hiivmind-corpus-navigate | "polars lazy evaluation" |
| `/hiivmind-corpus refresh polars` | hiivmind-corpus-refresh | "polars" |
| `/hiivmind-corpus register github:hiivmind/hiivmind-corpus-flyio` | hiivmind-corpus-register | "github:hiivmind/hiivmind-corpus-flyio" |
| `/hiivmind-corpus` | (show menu) | |

---

## Available Skills

| Skill | Purpose |
|-------|---------|
| `hiivmind-corpus-init` | Create new corpus scaffold |
| `hiivmind-corpus-add-source` | Add documentation sources |
| `hiivmind-corpus-build` | Build/rebuild the index |
| `hiivmind-corpus-navigate` | Query documentation |
| `hiivmind-corpus-refresh` | Sync with upstream changes |
| `hiivmind-corpus-enhance` | Deepen coverage on topics |
| `hiivmind-corpus-discover` | List available corpora |
| `hiivmind-corpus-register` | Register corpus with project |
| `hiivmind-corpus-status` | Check corpus health/freshness |
| `hiivmind-corpus-graph` | View, validate, edit concept graphs |
| `hiivmind-corpus-bridge` | Cross-corpus concept bridges (deferred — schema defined, skill not yet implemented) |
