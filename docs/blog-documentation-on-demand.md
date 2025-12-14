# Documentation on Demand: Injecting Knowledge Into Claude Code

Every time I work with a library that's newer than Claude's training data—or just not popular enough to be well-represented—I hit the same wall. Claude confidently suggests APIs that don't exist, patterns that were deprecated six months ago, or completely misses features that would solve my problem in one line.

The standard solutions don't cut it:
- **Web search** returns blog posts from 2022 and Stack Overflow answers for the wrong version
- **Fetching docs** one URL at a time loses context about what's actually relevant
- **Hoping it's in training data** is gambling

I wanted something different: inject authoritative documentation directly into Claude Code's working context, on demand, for any library. Build it once in a few minutes, keep it fresh automatically, and have it available whenever I need it.

That's what hiivmind-corpus does. And the pattern scales further than I initially expected.

## The Speed Surprised Me

I expected building a documentation corpus to be a chore—manually organizing hundreds of docs, writing descriptions, maintaining structure. The reality:

**2-3 minutes.** Sometimes less.

```
/hiivmind-corpus polars

> Cloning pola-rs/polars...
> Found 847 documentation files across 12 directories.
> What areas matter most to you?

"Data modeling and lazy evaluation. Skip deployment stuff."

> Here's a draft index with 45 entries across 8 sections...
> [shows draft]

"Looks good. Add more detail on expressions."

> Added 12 expression entries. Ready to save.
```

That's it. The corpus exists. Next time I ask "how do I filter nulls in Polars?", Claude reads from the index, fetches the actual docs, and gives me current information with file citations.

The speed comes from collaborative building. Claude does the heavy lifting—scanning files, identifying topics, drafting descriptions—while I provide judgment about what matters. My expertise steers; Claude executes.

## Many Corpora, Zero Overhead

Once I had one corpus working, I wanted more. Polars, Ibis, Narwhals, Substrait—the modern data stack isn't well-represented in training data, but it's all excellently documented.

The problem: how do I manage many corpora without overhead? Which one should Claude use when I ask a question?

The solution: **per-session discovery with self-describing corpora.**

```
Session starts
    ↓
First docs question
    ↓
Discover all installed corpora (4 locations)
    ↓
Read keywords from each corpus's config.yaml
    ↓
Build in-memory routing table
    ↓
Match query → route to correct corpus
```

Each corpus declares its own routing keywords:

```yaml
# data/config.yaml in hiivmind-corpus-polars
project_name: polars
display_name: Polars
keywords:
  - polars
  - dataframe
  - lazy
  - expression
  - series
```

Install a new corpus from a marketplace, it's discoverable next session. Uninstall one, it's gone. No central registry to maintain, no config files to update. Corpora are self-contained and self-describing.

Ask "how do I do a lazy join?" and Claude routes to Polars. Ask "what's the Ibis equivalent?" and it routes to Ibis. No friction.

## The Real Power: Embedded Corpora

General-purpose corpora are useful. But the pattern gets really interesting when you embed a corpus into a specialized tool.

Consider an API explorer skill—something that helps you work with a specific API like GitHub's. It needs to know:
- What endpoints exist (REST and GraphQL)
- What parameters they take
- How operations relate to each other
- The actual syntax for making calls

You could hardcode this. Or you could embed a corpus:

```
┌─────────────────────────────────────────────┐
│  GitHub API Explorer Skill                  │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Embedded Corpus                    │   │
│  │                                     │   │
│  │  • REST docs from github/docs       │   │
│  │  • GraphQL schema with search       │   │
│  │  • Entry keywords match API vocab   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  "Create a milestone" →                     │
│    Keywords match: milestones, POST, create │
│    Fetch: rest:repos/milestones.md#create   │
│    Execute with current syntax              │
└─────────────────────────────────────────────┘
```

The corpus becomes the skill's built-in knowledge base. It knows where to look, what vocabulary to match, and always has current documentation.

This is the pattern we're building with hiivmind-pulse-gh—GitHub automation skills backed by a corpus of GitHub's API documentation. The skill operates; the corpus knows.

## Two Levels of Keywords

For this to work smoothly, we designed a two-level keyword system:

| Level | Purpose | Example |
|-------|---------|---------|
| **Corpus-level** | Route to the right corpus | `polars`, `dataframe`, `lazy` |
| **Entry-level** | Find the right entry | `milestones`, `POST`, `create`, `due_on` |

Corpus-level keywords live in `config.yaml` and handle routing between corpora. Entry-level keywords live inline in the index:

```markdown
## Milestones

### REST Operations
- **Create Milestone** `rest:repos/milestones.md#create` - Create a new milestone
  Keywords: `milestones`, `POST`, `create`, `title`, `due_on`
```

When a skill knows its domain vocabulary—the terms users and routing guides actually use—it can match queries precisely. "Set a due date on milestone" matches `milestones`, `due_on` and routes to exactly the right documentation.

## What This Unlocks

The combination of fast corpus creation, per-session discovery, and embedded corpora unlocks something powerful:

**Any well-documented library becomes a first-class citizen in Claude Code.**

The library doesn't need to be popular. It doesn't need to be in training data. It just needs docs. Clone them, build an index in 2-3 minutes, and Claude works with it like it's always known it.

For esoteric libraries, niche tools, internal documentation—anything with good docs but poor LLM coverage—this levels the playing field.

And for specialized tools that embed their own corpus: they become domain experts. Not "Claude that can look things up" but "Claude that deeply knows this domain and operates fluently within it."

## The Pattern, Generalized

The corpus approach is really a specific instance of a broader pattern:

**Human-curated indexes + LLM retrieval + file-based state = domain expertise without infrastructure**

Curated indexes beat auto-generated ones because human judgment about what matters is valuable. LLM retrieval beats vector search for document-scale corpora because Claude can read and reason about the index directly. File-based state beats databases because it's portable, versionable, and transparent.

Put them together and you get expertise injection. Pick a domain, invest 2-3 minutes, gain a knowledgeable assistant for that domain permanently.

## Getting Started

If you want to try this:

1. **Install the meta-plugin:**
   ```
   /plugin marketplace add hiivmind/hiivmind-corpus
   /plugin install hiivmind-corpus@hiivmind
   ```

2. **Create a corpus for any library:**
   ```
   /hiivmind-corpus
   > "Create a corpus for [library name]"
   ```

3. **Use it:**
   ```
   "How do I [do something] in [library]?"
   ```

The corpus handles the rest—routing, fetching, citing.

Or install pre-built corpora from the marketplace:
- `hiivmind-corpus-polars` - Polars DataFrame library
- `hiivmind-corpus-ibis` - Ibis portable DataFrame API
- `hiivmind-corpus-narwhals` - Narwhals DataFrame-agnostic interface
- `hiivmind-corpus-claude-agent-sdk` - Claude Agent SDK

## The Bigger Picture

We're in an interesting moment for AI tooling. LLMs are powerful but their knowledge is frozen at training time. RAG systems help but add infrastructure complexity. Web search helps but returns noise.

Corpus-based knowledge injection threads the needle: current information, zero infrastructure, human-curated quality. The cost is 2-3 minutes per library. The payoff is permanent domain expertise.

For anyone working with fast-moving libraries, niche tools, or building specialized AI assistants: this pattern is worth knowing.

Documentation is the raw material. Corpora are the refined product. Claude Code is the engine. Together, they're unstoppable.

---

*hiivmind-corpus is open source: [github.com/hiivmind/hiivmind-corpus](https://github.com/hiivmind/hiivmind-corpus)*
