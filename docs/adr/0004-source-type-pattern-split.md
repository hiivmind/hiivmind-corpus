---
adr: 4
title: "Split sources.md into Per-Type Pattern Files"
status: Accepted
date: 2025-12-18
deciders: [nathanielramm]
---

# 4. Split sources.md into Per-Type Pattern Files

## Status

Accepted (implemented 2025-12-18)

## Context

The `lib/corpus/patterns/sources.md` file has grown to 803 lines (~2,800 words) covering 4 source types with 53+ operations:

| Source Type | Lines | Operations | Purpose |
|-------------|-------|------------|---------|
| git | 252 | 14 | Clone, fetch, SHA tracking, change comparison |
| local | 47 | 3 | Upload directory management |
| web | 75 | 4 | Content caching, URL slugification |
| generated-docs | 197 | 7 | Hybrid git+web operations |
| shared utilities | 185 | 9 | URL parsing, existence checks, errors |

**Problems with the monolithic approach:**

1. **Violates progressive disclosure**: Skills loading the pattern get all 803 lines regardless of which source type they need
2. **Maintenance risk**: Editing git operations risks breaking web or generated-docs sections
3. **Navigation difficulty**: Finding relevant operations requires scrolling through unrelated content
4. **Growth trajectory**: Adding ADR-0003's generated-docs type added 197 lines; future types will compound the problem
5. **Reference imprecision**: Skills can only reference "sources.md" broadly, not specific type operations

**Current references (16 files):**
- 6 skills reference sources.md for different purposes
- 10 pattern/doc files cross-reference it
- Each reference context only needs a subset of operations

## Decision

Split `sources.md` into a `sources/` subdirectory with focused files per source type.

### New Directory Structure

```
lib/corpus/patterns/sources/
├── README.md           # Overview, taxonomy, when-to-use guide
├── git.md              # Git repository operations
├── local.md            # Local file uploads
├── web.md              # Web content caching
├── generated-docs.md   # Hybrid git+web operations
└── shared.md           # URL parsing, existence checks, errors
```

### Content Distribution

| New File | Content from sources.md | Estimated Lines |
|----------|------------------------|-----------------|
| `README.md` | Purpose, prerequisites, taxonomy table, examples, related patterns | ~150 |
| `git.md` | Git source operations (lines 32-283) | ~260 |
| `local.md` | Local source operations (lines 321-367) | ~60 |
| `web.md` | Web source operations (lines 368-442) | ~90 |
| `generated-docs.md` | Generated-docs operations (lines 443-639) | ~220 |
| `shared.md` | URL parsing, existence checks, cross-platform, errors | ~160 |

### Reference Strategy

| Context | Reference |
|---------|-----------|
| Multi-type skill (init, add-source) | `sources/README.md` |
| Git-specific operation | `sources/git.md` |
| Generated-docs operation | `sources/generated-docs.md` |
| Shared utilities (URL parsing) | `sources/shared.md` |

### Generated-Docs Hybrid Handling

The `generated-docs.md` file will:
- Declare explicit dependencies on `git.md` and `web.md`
- Cross-reference specific sections (e.g., `git.md#clone-a-git-repository`)
- Maintain all unique operations (URL discovery, live fetch)
- Not duplicate content from referenced files

## Consequences

### Positive

- **Focused files**: Each file covers one source type (~60-260 lines vs 803)
- **Precise references**: Skills can link to exact operations needed
- **Independent evolution**: Update git operations without touching web code
- **Better discoverability**: Directory structure shows available source types
- **Aligns with ADR-0002**: Progressive disclosure pattern for pattern library

### Negative

- **More files to navigate**: 6 files instead of 1
- **Cross-reference overhead**: generated-docs.md must reference git.md and web.md
- **Migration effort**: 17 files need reference updates

### Neutral

- **Introduces sources/ subdirectory**: First nested pattern directory
- **README.md as entry point**: Follows documentation conventions

## Implementation

**New files (6):**

| File | Purpose |
|------|---------|
| `lib/corpus/patterns/sources/README.md` | Overview and navigation |
| `lib/corpus/patterns/sources/git.md` | Git repository operations |
| `lib/corpus/patterns/sources/local.md` | Local file operations |
| `lib/corpus/patterns/sources/web.md` | Web caching operations |
| `lib/corpus/patterns/sources/generated-docs.md` | Hybrid operations |
| `lib/corpus/patterns/sources/shared.md` | Cross-type utilities |

**Files to update (17):**

| Category | Files | Reference Changes |
|----------|-------|-------------------|
| Skills | 6 files | Type-specific or README refs |
| Patterns | 7 files | Cross-reference updates |
| Docs | 3 files | Path updates |
| CLAUDE.md | 1 file | Architecture diagram |

**Files to delete (1):**
- `lib/corpus/patterns/sources.md` (after migration complete)

## References

- [ADR-0002: Skill Refactoring for Progressive Disclosure](0002-skill-refactoring-for-progressive-disclosure.md)
- [ADR-0003: Generated-Docs Source Type](0003-generated-docs-source-type.md)
