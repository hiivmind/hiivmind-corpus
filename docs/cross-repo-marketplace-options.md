# Cross-Repository Marketplace Options for hiivmind Corpus Plugins

**Date:** 2025-12-21
**Context:** Exploring options for creating a parent marketplace that can reference and install corpus plugins from separate GitHub repositories

---

## Problem Statement

The hiivmind organization maintains multiple corpus plugin repositories:
- `hiivmind-corpus-data` - Data engineering libraries (Polars, Ibis, Narwhals, Substrait)
- `hiivmind-corpus-claude` - Claude-related projects (Agent SDK)
- `hiivmind-corpus-github` - GitHub API documentation
- Future corpus repositories as the collection grows

**Goal:** Create a unified entry point (parent marketplace) that can reference and install plugins from these separate repositories, providing users with:
1. Single installation point for all hiivmind corpora
2. Automatic dependency resolution
3. Maintained independence of individual corpus repositories

---

## Current Claude Code Plugin System Limitations

### Marketplace.json Format

The `marketplace.json` file currently **only supports relative paths** within the same repository:

```json
{
  "name": "hiivmind-corpus-data",
  "plugins": [
    {
      "name": "hiivmind-corpus-polars",
      "source": "./hiivmind-corpus-polars",  // ← Must be relative path
      "description": "...",
      "version": "1.0.0"
    }
  ]
}
```

**Not supported:**
- ❌ External repository URLs
- ❌ GitHub references (e.g., `github:hiivmind/repo`)
- ❌ Cross-repository paths
- ❌ HTTP/HTTPS URLs to remote plugins

**Path requirements:**
- Must be relative paths starting with `./`
- Must point to subdirectories within the same repository
- No absolute paths or parent directory navigation (`../`)

---

## GitHub Repository Composition Features

### Git Submodules (Fully Supported)

GitHub provides **native support for Git submodules** via GraphQL API:

**GraphQL Schema:**
```graphql
type Submodule {
  branch: String              # Tracking branch for updates
  gitUrl: URI!                # URL of the submodule repository
  name: String!               # Name in .gitmodules
  path: String!               # Path in the superproject
  subprojectCommitOid: String # Commit revision being tracked
}

type Repository {
  # Returns submodules from default branch HEAD
  submodules(first: Int): SubmoduleConnection!
}

type Commit {
  # Returns submodules at specific commit
  submodules(first: Int): SubmoduleConnection!
}

type TreeEntry {
  # If directory is a submodule, returns submodule info
  submodule: Submodule
}
```

**GitHub UI Support:**
- Submodules visible in repository file browser
- Shows commit SHA being tracked
- Links to external repository
- Tracks .gitmodules file changes

**Git Operations:**
```bash
# Add submodule
git submodule add https://github.com/hiivmind/hiivmind-corpus-data

# Clone with submodules
git clone --recursive https://github.com/hiivmind/hiivmind-corpus-meta

# Update submodules
git submodule update --init --recursive
```

### Git Subtree (Alternative)

Git subtree is another option but:
- Less widely supported in GitHub UI
- Merges external repo into parent history
- No GraphQL API support
- More complex to maintain

**Not recommended for this use case.**

---

## Available Options

### Option 1: Plugin Dependencies (Recommended)

Create a meta-plugin that declares dependencies on separate marketplace plugins.

**Implementation:**

```json
// hiivmind-corpus-meta/.claude-plugin/plugin.json
{
  "name": "hiivmind-corpus-meta",
  "version": "1.0.0",
  "description": "Parent plugin that installs all hiivmind corpus collections",
  "dependencies": {
    "plugins": [
      "hiivmind-corpus-data@hiivmind-corpus-data",
      "hiivmind-corpus-claude@hiivmind-corpus-claude",
      "hiivmind-corpus-github@hiivmind-corpus-github"
    ]
  }
}
```

**Format:** `"plugin-name@marketplace-name"`

**How it works:**
1. User installs `hiivmind-corpus-meta`
2. Claude Code automatically installs all dependent plugins
3. Each marketplace repository remains independent
4. Dependencies update independently

**Pros:**
- ✅ Works with current Claude Code plugin system
- ✅ Separate repos for each marketplace (clean development)
- ✅ Single entry point for users
- ✅ Automatic dependency installation
- ✅ No git complexity for users
- ✅ Aligns with how `hiivmind-pulse-gh` handles external corpus dependency

**Cons:**
- ⚠️ Users see multiple installed plugins (not unified marketplace view)
- ⚠️ Need to verify `dependencies.plugins` feature is fully implemented
- ⚠️ Each plugin requires separate publication/distribution

**Status:** Found in ADR-003 for hiivmind-pulse-gh but not yet implemented. Needs verification of Claude Code support.

---

### Option 2: Git Submodules + Flattened Structure

Use git submodules to aggregate separate repositories, then flatten into single marketplace.

**Structure:**

```
hiivmind-corpus-meta/
├── .gitmodules                           # Submodule definitions
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json                  # References all flattened plugins
├── scripts/
│   └── flatten-marketplaces.sh           # Extracts plugins from nested marketplaces
│
├── hiivmind-corpus-data/                 # Submodule (original marketplace)
│   ├── .claude-plugin/marketplace.json
│   ├── hiivmind-corpus-polars/
│   ├── hiivmind-corpus-ibis/
│   └── ...
│
├── hiivmind-corpus-claude/               # Submodule (original marketplace)
│   └── ...
│
├── hiivmind-corpus-github/               # Submodule (original marketplace)
│   └── ...
│
├── hiivmind-corpus-polars/               # Flattened (copied from submodule)
├── hiivmind-corpus-ibis/                 # Flattened (copied from submodule)
├── hiivmind-corpus-narwhals/             # Flattened (copied from submodule)
└── hiivmind-corpus-claude-agent-sdk/     # Flattened (copied from submodule)
```

**Implementation:**

```bash
#!/bin/bash
# scripts/flatten-marketplaces.sh

# Extract plugins from nested marketplaces into flat structure
for marketplace in hiivmind-corpus-*; do
  if [ -f "$marketplace/.claude-plugin/marketplace.json" ]; then
    # Copy each plugin subdirectory
    for plugin in "$marketplace"/hiivmind-corpus-*; do
      if [ -d "$plugin" ]; then
        plugin_name=$(basename "$plugin")
        echo "Flattening $plugin_name from $marketplace"
        cp -r "$plugin" "./$plugin_name"
      fi
    done
  fi
done

# Generate parent marketplace.json from all flattened plugins
# (Script to generate this programmatically)
```

**Pros:**
- ✅ Works with current marketplace.json format
- ✅ Maintains separate development repos (via submodules)
- ✅ Native GitHub feature (visible in UI, GraphQL API support)
- ✅ Single unified marketplace for users
- ✅ Can pin submodules to specific commits or track branches

**Cons:**
- ❌ Submodule management complexity
- ❌ Requires flattening script
- ❌ Duplication of plugin files (submodule + flattened copy)
- ❌ Users need `git clone --recursive` or manual submodule init
- ❌ Build/release step required to flatten structure
- ❌ Synchronization needed between submodules and flattened copies

---

### Option 3: Monorepo (All Plugins in One Repository)

Consolidate all corpus plugins into a single repository with flat structure.

**Structure:**

```
hiivmind-corpus-all/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json                  # All plugins listed
├── hiivmind-corpus-polars/
├── hiivmind-corpus-ibis/
├── hiivmind-corpus-narwhals/
├── hiivmind-corpus-substrait/
├── hiivmind-corpus-claude-agent-sdk/
└── hiivmind-corpus-github-docs/
```

**Pros:**
- ✅ Simplest marketplace.json configuration
- ✅ No submodule or dependency complexity
- ✅ Single repository to maintain
- ✅ Easiest for users to install

**Cons:**
- ❌ Loses repository independence
- ❌ Single git history for all plugins
- ❌ Harder to manage different release cycles
- ❌ Requires migrating existing repositories
- ❌ Breaks existing plugin installations
- ❌ All contributors need access to entire monorepo

**Not recommended** - destroys the organizational benefits of separate repositories.

---

### Option 4: Proxy/Gateway Plugin (Minimal Meta-Plugin)

Create a minimal plugin that acts as documentation/gateway, directing users to install specific marketplace plugins.

**Structure:**

```
hiivmind-corpus-gateway/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── corpus-installer/
│       └── SKILL.md                      # Interactive installer
└── README.md                             # Lists available marketplaces
```

**SKILL.md example:**

```markdown
---
name: Corpus Installer
description: Interactive installer for hiivmind corpus plugins
---

This skill helps you discover and install hiivmind corpus plugins.

## Available Marketplaces

1. **hiivmind-corpus-data** - Data engineering libraries
   - Polars, Ibis, Narwhals, Substrait
   - Install: `/plugin install hiivmind-corpus-data@hiivmind-corpus-data`

2. **hiivmind-corpus-claude** - Claude-related projects
   - Claude Agent SDK
   - Install: `/plugin install hiivmind-corpus-claude@hiivmind-corpus-claude`

3. **hiivmind-corpus-github** - GitHub API documentation
   - Install: `/plugin install hiivmind-corpus-github@hiivmind-corpus-github`

The skill can use AskUserQuestion to help users select which marketplaces to install.
```

**Pros:**
- ✅ No technical complexity
- ✅ Maintains repository independence
- ✅ Easy to maintain
- ✅ Educational for users

**Cons:**
- ❌ Not automatic installation
- ❌ Requires user interaction
- ❌ Not a true "parent marketplace"
- ❌ Manual installation commands

---

## Feature Request: Enhanced marketplace.json

**Proposal:** Extend marketplace.json to support external repository references.

```json
{
  "name": "hiivmind-corpus-meta",
  "plugins": [
    {
      "name": "hiivmind-corpus-polars",
      "source": "github:hiivmind/hiivmind-corpus-data/hiivmind-corpus-polars",
      "version": "1.0.0"
    },
    {
      "name": "hiivmind-corpus-claude-agent-sdk",
      "source": "https://github.com/hiivmind/hiivmind-corpus-claude/hiivmind-corpus-claude-agent-sdk",
      "version": "1.0.0"
    }
  ]
}
```

**Required changes to Claude Code:**
- Extend marketplace.json source field to accept URLs
- Implement remote plugin fetching
- Handle version pinning for external plugins
- Dependency resolution across repositories

**Status:** Not currently supported. Would require feature request to Claude Code development team.

---

## Recommendation Matrix

| Criteria | Plugin Dependencies | Git Submodules | Monorepo | Gateway Plugin |
|----------|-------------------|----------------|----------|----------------|
| Repository independence | ✅ Excellent | ✅ Excellent | ❌ Lost | ✅ Excellent |
| User experience | ✅ Automatic | ⚠️ Requires git knowledge | ✅ Simple | ⚠️ Manual |
| Maintenance overhead | ⚠️ Medium | ❌ High | ✅ Low | ✅ Low |
| Works with current system | ⚠️ Needs verification | ✅ Yes (with workarounds) | ✅ Yes | ✅ Yes |
| True unified marketplace | ⚠️ No (multiple plugins) | ✅ Yes | ✅ Yes | ❌ No |
| Automatic installation | ✅ Yes | ⚠️ Requires build step | ✅ Yes | ❌ No |

---

## Recommended Approach

### Primary: Plugin Dependencies (Option 1)

**Reasoning:**
1. Aligns with existing ADR-003 pattern from hiivmind-pulse-gh
2. Cleanest separation of concerns
3. Best developer experience
4. Minimal user complexity

**Action Items:**
1. Verify `dependencies.plugins` feature is implemented in Claude Code
2. Create `hiivmind-corpus-meta` plugin with dependency declarations
3. Test installation workflow
4. Document for users

**Example implementation:**

```json
// hiivmind-corpus-meta/.claude-plugin/plugin.json
{
  "name": "hiivmind-corpus-meta",
  "version": "1.0.0",
  "description": "Unified installation for all hiivmind documentation corpora",
  "author": {
    "name": "hiivmind"
  },
  "repository": "https://github.com/hiivmind/hiivmind-corpus-meta",
  "dependencies": {
    "plugins": [
      "hiivmind-corpus-data@hiivmind-corpus-data",
      "hiivmind-corpus-claude@hiivmind-corpus-claude",
      "hiivmind-corpus-github@hiivmind-corpus-github"
    ]
  }
}
```

### Fallback: Gateway Plugin (Option 4)

If plugin dependencies are not yet implemented, create a minimal gateway plugin that:
- Documents all available corpus marketplaces
- Provides installation commands
- Offers interactive skill for marketplace selection
- Acts as entry point until dependencies are supported

---

## Implementation Verification Needed

Before proceeding, verify:

1. **Plugin dependency support:**
   - Does Claude Code support `dependencies.plugins` field?
   - Test with simple example
   - Check if automatic installation works

2. **Marketplace installation:**
   - Can plugins reference other plugins by marketplace name?
   - Format: `plugin-name@marketplace-name`
   - Does version pinning work?

3. **Update behavior:**
   - How do dependent plugins update?
   - Can users update individual dependencies?
   - What happens if dependency is already installed?

---

## References

- ADR-003: External Corpus Dependency (`hiivmind-pulse-gh/docs/adrs/003-external-corpus-dependency.md`)
- GitHub GraphQL Submodule API (schema.docs.graphql:60266-60341)
- Claude Code Plugin Structure (`plugin-dev` skills)
- Existing marketplace implementations:
  - `hiivmind-corpus-data/.claude-plugin/marketplace.json`
  - `hiivmind-corpus-claude/.claude-plugin/marketplace.json`
  - `hiivmind-pulse-gh/.claude-plugin/marketplace.json`

---

## Next Steps

1. **Verify plugin dependency feature** - Test if `dependencies.plugins` is implemented
2. **Create proof-of-concept** - Build minimal meta-plugin to test approach
3. **Document installation workflow** - Write user-facing documentation
4. **Consider feature request** - If dependencies don't work, propose enhanced marketplace.json to Claude Code team
5. **Implement chosen solution** - Roll out parent marketplace plugin
