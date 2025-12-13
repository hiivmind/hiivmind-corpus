# How I Built hiivmind-corpus: Zero-Infrastructure Agent Patterns

Most agent architectures look like this: vector databases for retrieval, Redis for state, external APIs for embeddings, orchestration frameworks, deployment infrastructure. By the time you've scaffolded everything, you've spent more time on plumbing than on solving the actual problem.

hiivmind-corpus takes a different approach. It's a complex multi-skill system—eight specialized skills with a natural language gateway, shared libraries, and persistent state—but it runs entirely on files. No databases. No servers. No API keys. Just markdown, YAML, and git.

Here's how it works and why these patterns might be useful for your own agent architectures.

## The Problem

Claude Code is powerful, but it has a documentation problem. When you ask about a library like Polars or React, Claude draws from:

1. **Training data** — Potentially months or years out of date
2. **Web search** — Hit or miss, often finds outdated tutorials
3. **URL fetching** — One page at a time, no context about what's relevant

For fast-moving libraries, this means Claude regularly hallucinates APIs, suggests deprecated patterns, or misses features entirely.

I wanted persistent, curated documentation that Claude could search directly—like Claude Projects on claude.ai, but without the context overhead and with proper maintenance tools.

## The Architecture

```
/hiivmind-corpus (gateway command)
        │
        ├── discover ──► find installed corpora
        ├── navigate ──► query across corpora
        └── init ──────► create new corpus
                              │
                    add-source → build → enhance
                                           │
                              refresh ◄────┘
                                 │
                              upgrade
```

One command, eight skills, natural language routing. Say what you want, get routed to the right skill.

## Pattern 1: Gateway Command as Coordinator

Most agent systems have a "coordinator" or "router" that decides which specialized agent handles a request. The typical implementation involves embeddings, intent classification models, or complex routing logic.

hiivmind-corpus uses a simpler approach: a markdown file with examples.

```markdown
# /hiivmind-corpus gateway command

Detect user intent from natural language and route to appropriate skill:

| Intent | Route to |
|--------|----------|
| Create/init/new corpus | hiivmind-corpus-init |
| What corpora/list/installed | hiivmind-corpus-discover |
| Question about docs/how do I | hiivmind-corpus-navigate |
| Refresh/update/sync | hiivmind-corpus-refresh |
| ...
```

Claude reads this, understands the intent from context, and invokes the right skill. No embeddings, no classifier—just clear examples that Claude can pattern-match against.

**Why this works:** LLMs are already excellent at intent classification when given clear examples. Adding infrastructure for what the model does natively is over-engineering.

## Pattern 2: Skills as Focused Agents

Each skill has a single responsibility and clear boundaries:

| Skill | Does | Does NOT |
|-------|------|----------|
| init | Create directory structure, clone repos | Build indexes, answer questions |
| build | Create index collaboratively | Clone repos, refresh from upstream |
| navigate | Answer questions from index | Modify the index |
| refresh | Update index from upstream changes | Create new corpora |

This isn't just good software design—it's essential for agent reliability. When a skill's scope is narrow, its SKILL.md instructions can be precise. When scope creeps, instructions become vague and the agent improvises (often badly).

**The key insight:** Each skill ends with an explicit handoff. `init` finishes with "recommend running `build` next." `build` finishes with "the corpus is ready; use `navigate` to query." This prevents skills from scope-creeping into each other's territory.

## Pattern 3: File-Based State

The entire state of a corpus is three files:

```
data/
├── config.yaml      # Sources, SHAs, timestamps
├── index.md         # Topic → file mappings
└── project-awareness.md  # Snippet for CLAUDE.md
```

That's it. No database queries, no state management library, no serialization concerns. Read a file, parse YAML or markdown, done.

**config.yaml tracks freshness:**
```yaml
sources:
  - id: polars
    type: git
    repo_url: https://github.com/pola-rs/polars
    branch: main
    last_commit_sha: abc123
    last_indexed_at: "2025-12-13"
```

When `refresh` runs, it compares `last_commit_sha` to current HEAD. If different, it fetches the diff and updates the index. Simple, transparent, debuggable.

**Why files over databases:**
- **Portable** — Clone the repo, you have everything
- **Versionable** — Git tracks every change to your index
- **Human-readable** — Debug by opening a file, not querying a DB
- **No infrastructure** — No connection strings, no migrations, no backups

## Pattern 4: Composable Shell Library

The skills share common operations: finding corpora, checking freshness, resolving paths. Rather than duplicate this logic, there's a shell function library:

```bash
source "${CLAUDE_PLUGIN_ROOT}/lib/corpus/corpus-discovery-functions.sh"

# Pipe-first composition
discover_all | filter_built | list_names
```

Functions are small, focused, and compose via pipes—the Unix philosophy applied to agent tooling.

**Why shell over Python/TypeScript:**
- Zero dependencies (bash is everywhere)
- Claude can read and invoke directly
- Pipes are natural for data transformation
- Easy to test interactively

## Pattern 5: Human-Curated Over Auto-Generated

The index isn't auto-generated from file contents. It's built collaboratively:

```
Claude: "I found 847 documentation files. What areas matter most to you?"
User: "Data modeling and query optimization. Skip the deployment docs."
Claude: "Got it. Here's a draft index focused on those areas..."
```

This takes 1-2 minutes, even for enormous documentation sets—and it's basically free. Compare that to embeddings, where you're paying per token to process thousands of documents, plus ongoing costs for the vector database.

**The tradeoff isn't time or money—it's control.** Auto-indexing gives you generic coverage. Collaborative building gives you an index shaped by your actual priorities. The latter is more useful.

## Pattern 6: Graceful Degradation

Every skill handles missing state gracefully:

- No local clone? Fall back to raw GitHub URLs
- Index is stale? Warn but still answer
- Config missing a field? Use sensible defaults

This matters because real-world state is messy. Users delete folders, partially complete workflows, have old versions. Agents that crash on imperfect state are fragile; agents that adapt are useful.

## What's Different From Typical Agent Architectures

| Typical Approach | hiivmind-corpus |
|------------------|-----------------|
| Vector DB for retrieval | Markdown index searched by Claude directly |
| Embeddings API ($$$) | Free—Claude reads the index |
| Redis/DB for state | YAML and markdown files in git |
| Orchestration framework | Gateway command with example-based routing |
| Intent classification model | Claude's native understanding + clear examples |
| Auto-indexing | Human-curated in 1-2 minutes |
| Deployment infrastructure | Just files—clone and use |

## When This Approach Works

This architecture fits when:

1. **State is naturally document-shaped** — configs, indexes, logs
2. **Human curation adds value** — the user's judgment matters
3. **Portability matters** — sharing via git, no account required
4. **Transparency matters** — users need to see and edit state
5. **Infrastructure is a liability** — every service is a failure point
6. **Cost matters** — no per-query embedding costs

## When It Doesn't

Use traditional infrastructure when:

1. **Sub-second latency is critical** — file I/O adds overhead
2. **State is relational** — complex queries need a real database
3. **Scale is massive** — millions of documents need vector search
4. **No human in the loop** — fully automated pipelines

## The Bigger Point

Most agent complexity is accidental, not essential. We reach for infrastructure because that's what "serious" systems use, not because the problem requires it.

hiivmind-corpus handles eight specialized skills, natural language routing, persistent state, multi-source corpora, freshness tracking, and collaborative building—with zero external dependencies beyond git.

Before adding that vector database or spinning up that orchestration service, ask: could this just be files?

Often, the answer is yes.

---

*hiivmind-corpus is open source: [github.com/hiivmind/hiivmind-corpus](https://github.com/hiivmind/hiivmind-corpus)*
