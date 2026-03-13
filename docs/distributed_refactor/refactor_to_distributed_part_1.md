# Architectural Blueprint: hiivmind-corpus Ecosystem

## Vision

A distributed documentation corpus ecosystem with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     hiivmind-corpus Ecosystem                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌────────────────────────────────────────────┐                    │
│   │           hiivmind-corpus (plugin)          │                    │
│   │                                             │                    │
│   │   BUILD                    READ             │                    │
│   │   ─────                    ────             │                    │
│   │   • init                   • navigate       │                    │
│   │   • add-source             • discover       │                    │
│   │   • build                  • status         │                    │
│   │   • refresh                • register       │                    │
│   │   • enhance                                 │                    │
│   │   • upgrade                                 │                    │
│   │                                             │                    │
│   └────────────────────┬────────────────────────┘                    │
│                        │                                             │
│            PRODUCES    │    CONSUMES                                 │
│                        ▼                                             │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │              Data-Only Corpus Repositories               │       │
│   │                                                          │       │
│   │  github.com/hiivmind/hiivmind-corpus-flyio              │       │
│   │  github.com/hiivmind/hiivmind-corpus-polars             │       │
│   │  github.com/hiivmind/hiivmind-corpus-claude-sdk         │       │
│   │  github.com/yourorg/internal-api-corpus                 │       │
│   │                                                          │       │
│   │  Each contains:                                          │       │
│   │    • config.yaml  (source definitions + keywords)        │       │
│   │    • index.md     (main index)                           │       │
│   │    • index-*.md   (sub-indexes for tiered corpora)       │       │
│   └─────────────────────────────────────────────────────────┘       │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │              Per-Project Configuration                    │       │
│   │                                                          │       │
│   │  .hiivmind/corpus/registry.yaml                         │       │
│   │    - Which corpora are relevant to this project          │       │
│   │    - Source locations (GitHub refs or local paths)       │       │
│   │    - Caching preferences (per corpus)                    │       │
│   └─────────────────────────────────────────────────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Key insight:** One plugin (`hiivmind-corpus`) handles both building AND reading corpora. Skills like `discover` and `status` serve both use cases.

---

## Component Breakdown

### 1. hiivmind-corpus (Single Plugin)

**Purpose:** Build, maintain, AND navigate documentation corpora

**Repository:** `github.com/hiivmind/hiivmind-corpus`

**Skills - BUILD:**
| Skill | Purpose |
|-------|---------|
| `hiivmind-corpus-init` | Initialize a new corpus repo |
| `hiivmind-corpus-add-source` | Add documentation sources |
| `hiivmind-corpus-build` | Build/rebuild the index |
| `hiivmind-corpus-refresh` | Update index from upstream changes |
| `hiivmind-corpus-enhance` | Deepen coverage on specific topics |
| `hiivmind-corpus-upgrade` | Migrate corpus to new schema versions |

**Skills - READ (NEW):**
| Skill | Purpose |
|-------|---------|
| `hiivmind-corpus-navigate` | Search corpus index, fetch documentation |
| `hiivmind-corpus-register` | Add a corpus to project registry |

**Skills - SHARED:**
| Skill | Purpose |
|-------|---------|
| `hiivmind-corpus-discover` | List registered/available corpora (EXISTS - enhance) |
| `hiivmind-corpus-status` | Check corpus freshness, registry health (NEW) |

**Changes needed:**
- Add `hiivmind-corpus-navigate` skill
- Add `hiivmind-corpus-register` skill
- Add `hiivmind-corpus-status` skill
- Enhance `hiivmind-corpus-discover` to work with registry
- Update `hiivmind-corpus-init` to create data-only structure
- Add registry patterns to `lib/corpus/patterns/`

---

### 3. Data-Only Corpus Repositories

**Purpose:** Store documentation indexes (no runtime logic)

**Structure:**
```
hiivmind-corpus-{name}/
├── config.yaml              # Source definitions, keywords
├── index.md                 # Main index
├── index-{section}.md       # Sub-indexes (tiered corpora)
├── .source/                 # Local clone cache (gitignored)
└── README.md                # Human documentation
```

**config.yaml schema:**
```yaml
schema_version: 2

corpus:
  name: "flyio"
  display_name: "Fly.io"
  keywords:
    - flyio
    - fly.io
    - deployment
    - hosting
    - machines
    - flyctl

sources:
  - id: flyio
    type: git
    repo_url: https://github.com/superfly/docs
    branch: main
    docs_root: "."
    last_commit_sha: "abc123..."
    last_indexed_at: "2026-01-08T12:00:00Z"

index:
  format: markdown
  tiered: true
  sub_indexes:
    - index-getting-started.md
    - index-apps.md
    - index-machines.md
```

---

### 4. Per-Project Registry

**Purpose:** Register which corpora are relevant to a project

**Location:** `.hiivmind/corpus/registry.yaml`

**Schema:**
```yaml
schema_version: 1

corpora:
  - id: flyio
    source:
      type: github
      repo: hiivmind/hiivmind-corpus-flyio
      ref: main                    # branch, tag, or commit
    cache:
      strategy: clone              # clone | fetch | none
      path: .corpus-cache/flyio    # local cache location
      ttl: 7d                      # refresh interval

  - id: polars
    source:
      type: github
      repo: hiivmind/hiivmind-corpus-data
      path: hiivmind-corpus-polars # subdirectory
      ref: v2.0.0

  - id: internal
    source:
      type: local
      path: ./docs/corpus
```

---

## Navigation Flow

```
User: "How do I deploy to fly.io?"
         │
         ▼
┌─────────────────────────────────────────┐
│  hiivmind-corpus-navigate               │
│                                         │
│  1. Read .hiivmind/corpus/registry.yaml │
│  2. Match "fly.io" to corpus keywords   │
│     → matches: flyio                    │
│  3. Fetch flyio index from GitHub       │
│     (or read from local cache)          │
│  4. Search index for "deploy"           │
│     → found: flyio:getting-started/...  │
│  5. Fetch documentation file            │
│  6. Present answer with citation        │
└─────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Add Read Skills to hiivmind-corpus

Add new skills for reading/navigating corpora:

**New skills:**
```
hiivmind-corpus/skills/
├── hiivmind-corpus-navigate/     # NEW
│   ├── SKILL.md
│   └── workflow.yaml
├── hiivmind-corpus-register/     # NEW
│   └── SKILL.md
├── hiivmind-corpus-status/       # NEW
│   └── SKILL.md
└── hiivmind-corpus-discover/     # ENHANCE
    └── SKILL.md                   # Add registry awareness
```

**New patterns:**
```
hiivmind-corpus/lib/corpus/patterns/
├── registry-loading.md           # NEW
├── index-fetching.md             # NEW
└── corpus-routing.md             # NEW
```

### Phase 2: Simplify Existing Corpus Repos

Convert existing corpus plugins to data-only:

**hiivmind-corpus-flyio:**
- DELETE: `.claude-plugin/`, `skills/`, `commands/`, `references/`
- MOVE: `data/*` → root
- UPDATE: `CLAUDE.md`, `README.md`

**hiivmind-corpus-data/** (mono-repo):
- Same pattern for polars, ibis, narwhals, substrait

**hiivmind-corpus-claude/**:
- Same pattern for claude-agent-sdk

### Phase 3: Update hiivmind-corpus-init

- Update templates to create data-only structure
- No more `skills/`, `commands/`, `.claude-plugin/` in output
- Add registry entry generation helper

### Phase 4: Migration Guide

Create migration guide for existing users:
1. Update `hiivmind-corpus` plugin (single plugin now does everything)
2. Create `.hiivmind/corpus/registry.yaml`
3. Register existing corpora with `/hiivmind-corpus register`
4. Old corpus plugins become data-only repos (no behavior)

---

## Benefits of This Architecture

| Aspect | Before | After |
|--------|--------|-------|
| **Maintenance** | Update navigation in every corpus | Update once in hiivmind-corpus |
| **Deployment** | Each corpus is a full plugin | Corpora are just data |
| **Dependencies** | Corpora need workflow framework | hiivmind-corpus has framework |
| **Size** | Heavy duplication | Minimal, DRY |
| **Flexibility** | Fixed navigation per corpus | Configurable per project |
| **Multi-corpus** | Separate plugins | Single plugin, multiple data sources |
| **Simplicity** | Two plugins (builder + reader) | One plugin does everything |

---

## Open Questions

1. **Corpus versioning:** How to handle corpus schema migrations when data repos are independent?

2. **Discovery across orgs:** How to discover available corpora beyond manually registering them?

3. **Gateway enhancement:** Should the existing `/hiivmind-corpus` gateway route to navigate/register/status as well as build skills?

---

## Files to Create/Modify

### Add to: hiivmind-corpus

| File | Action | Description |
|------|--------|-------------|
| `skills/hiivmind-corpus-navigate/SKILL.md` | CREATE | Navigate skill loader |
| `skills/hiivmind-corpus-navigate/workflow.yaml` | CREATE | Navigate workflow |
| `skills/hiivmind-corpus-register/SKILL.md` | CREATE | Register corpus to project |
| `skills/hiivmind-corpus-status/SKILL.md` | CREATE | Check corpus/registry health |
| `skills/hiivmind-corpus-discover/SKILL.md` | UPDATE | Add registry awareness |
| `lib/corpus/patterns/registry-loading.md` | CREATE | Pattern for registry access |
| `lib/corpus/patterns/index-fetching.md` | CREATE | Pattern for GitHub/local fetch |
| `lib/corpus/patterns/corpus-routing.md` | CREATE | Pattern for keyword matching |
| `skills/hiivmind-corpus-init/` | UPDATE | Data-only output templates |
| `CLAUDE.md` | UPDATE | Ecosystem documentation |
| `commands/hiivmind-corpus.md` | UPDATE | Add navigate/register/status routing |

### Modify: hiivmind-corpus-flyio

| File | Action |
|------|--------|
| `.claude-plugin/` | DELETE |
| `skills/` | DELETE |
| `commands/` | DELETE |
| `references/` | DELETE |
| `data/*` | MOVE to root |
| `CLAUDE.md` | UPDATE |
| `README.md` | UPDATE |

### Modify: Other corpus repos (same pattern)

- `hiivmind-corpus-data/hiivmind-corpus-polars/`
- `hiivmind-corpus-data/hiivmind-corpus-ibis/`
- `hiivmind-corpus-data/hiivmind-corpus-narwhals/`
- `hiivmind-corpus-claude/hiivmind-corpus-claude-agent-sdk/`

---

## Verification Plan

1. **Navigate skill works with registry:**
   - Create test `.hiivmind/corpus/registry.yaml` with flyio corpus
   - Run `/hiivmind-corpus navigate` with Fly.io question
   - Verify index fetch from GitHub
   - Verify documentation retrieval and citation

2. **Register skill works:**
   - Run `/hiivmind-corpus register github:hiivmind/hiivmind-corpus-flyio`
   - Verify registry.yaml created/updated
   - Verify corpus accessible via navigate

3. **Init creates data-only structure:**
   - Run `/hiivmind-corpus init` with new templates
   - Verify output has NO skills/commands/.claude-plugin
   - Verify config.yaml includes keywords field

4. **End-to-end flow:**
   - Build a corpus with `/hiivmind-corpus build`
   - Push to GitHub
   - Register with `/hiivmind-corpus register`
   - Navigate with `/hiivmind-corpus navigate`

5. **Gateway routes correctly:**
   - `/hiivmind-corpus build` → build skill
   - `/hiivmind-corpus navigate` → navigate skill
   - `/hiivmind-corpus register` → register skill
   - `/hiivmind-corpus status` → status skill
