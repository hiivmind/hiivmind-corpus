# ADR 0008: llms-txt Source Type

## Status

Accepted

## Context

Documentation sites are increasingly providing `llms.txt` manifests - markdown files at `/llms.txt` that list LLM-friendly content with direct links to raw markdown versions. This emerging standard provides:

1. **Structured discovery** - H1 title, optional blockquote summary, H2 sections with links
2. **Raw markdown access** - URLs point to `.md` versions (e.g., `/docs/skills.md` instead of `/docs/skills`)
3. **Change detection** - Hash the manifest to detect when content changes
4. **Size efficiency** - Raw markdown is 10-30x smaller than HTML SPA pages

### Examples Discovered

| Site | Manifest URL | Pages | Size Ratio |
|------|--------------|-------|------------|
| code.claude.com | `/docs/llms.txt` | 47 pages | 28KB vs 927KB (33x) |
| platform.claude.com | `/docs/llms.txt` | 532 pages (EN) | Similar ratio |
| vercel.com | `/llms.txt` | Hierarchical structure | N/A |

### llms.txt Standard Specification

From [llmstxt.org](https://llmstxt.org/):

```markdown
# Project Name             ← H1 title (required)

> Brief description        ← Blockquote summary (optional)

## Section Name            ← H2 sections with links

- [Page Title](url.md): Description of the page
- [Another Page](path/to/page.md): More details
```

**Key characteristics:**
- File at `/llms.txt` or `/docs/llms.txt`
- All URLs are relative or absolute with `.md` extension
- Sections group related content
- Optional summary in blockquote after title

### Comparison to Existing Source Types

| Feature | web | generated-docs | llms-txt |
|---------|-----|----------------|----------|
| Discovery | Manual URL list | Sitemap.xml | llms.txt manifest |
| Change detection | None (manual) | Git SHA | Manifest hash |
| Content format | HTML (large) | HTML (large) | Markdown (small) |
| Storage | `.cache/web/` | Live fetch | `.cache/llms-txt/` |
| Selective caching | Per-URL | Optional | Per-section or full |

## Decision

Add `llms-txt` as a new source type for sites providing llms.txt manifests.

### Config Schema

```yaml
- id: "claude-code-docs"
  type: "llms-txt"

  # Manifest location
  manifest:
    url: "https://code.claude.com/docs/llms.txt"
    last_hash: "sha256:abc123..."  # For change detection
    last_fetched_at: "2025-01-10T..."

  # URL configuration
  urls:
    base_url: "https://code.claude.com/docs/en"  # Prefix for relative URLs
    suffix: ".md"  # Append to URLs if not present

  # Caching strategy
  cache:
    enabled: true
    dir: ".cache/llms-txt/claude-code-docs/"
    strategy: "selective"  # "full" | "selective" | "on-demand"
    sections: ["skills", "agents"]  # Only cache these sections (if selective)

  # Discovered structure (populated on fetch)
  structure:
    title: "Claude Code"
    summary: "Anthropic's official CLI for Claude"
    sections:
      - name: "Getting Started"
        urls:
          - path: "getting-started/overview.md"
            title: "Overview"
          - path: "getting-started/installation.md"
            title: "Installation"
      - name: "Skills"
        urls:
          - path: "skills.md"
            title: "Skills"

  last_indexed_at: "2025-01-10T..."
```

### Rationale

1. **Manifest-driven discovery** - Parse llms.txt once, get structured URL list
2. **Hash-based change detection** - Lightweight check without cloning repos
3. **Raw markdown** - Dramatically smaller payloads, cleaner content
4. **Selective caching** - Only cache sections relevant to corpus focus
5. **Section awareness** - Index can mirror llms.txt sections

## Consequences

### Positive

- **Efficient caching** - 10-30x smaller files than HTML
- **Automatic discovery** - No manual URL enumeration
- **Easy change detection** - Hash comparison instead of git operations
- **Clean content** - No HTML extraction needed
- **Future-proof** - Growing adoption of llms.txt standard

### Negative

- **Limited adoption** - Not all sites provide llms.txt yet
- **Standard evolution** - llmstxt.org spec may change
- **Format variations** - Sites interpret spec differently (nested lists, etc.)

### Neutral

- **New source type** - Adds complexity to source taxonomy
- **Caching strategy decision** - User must choose full/selective/on-demand

## Alternatives Considered

1. **Extend `web` source type** - Rejected: Different enough to warrant new type (manifest-driven, markdown-native)
2. **Extend `generated-docs`** - Rejected: No git repo to track, fundamentally different change detection
3. **Auto-detect llms.txt in web source** - Rejected: Implicit behavior is confusing

## Implementation

### Files Modified

| Action | File | Description |
|--------|------|-------------|
| CREATE | `lib/corpus/patterns/sources/llms-txt.md` | Pattern documentation |
| MODIFY | `lib/corpus/patterns/sources/README.md` | Add to taxonomy |
| MODIFY | `skills/hiivmind-corpus-add-source/SKILL.md` | Manifest detection |
| MODIFY | `skills/hiivmind-corpus-build/SKILL.md` | Section suggestions |
| MODIFY | `skills/hiivmind-corpus-refresh/SKILL.md` | Hash-based freshness |
| MODIFY | `templates/navigate-skill.md.template` | Cache access pattern |
| MODIFY | `templates/config.yaml.template` | Example config |
| MODIFY | `CLAUDE.md` | Update source types list |

## Verification

1. **Manifest detection** - Add source to detect llms.txt at URLs
2. **Build with sections** - Use manifest sections as index suggestions
3. **Refresh with hash** - Detect manifest changes via hash comparison
4. **Navigate with cache** - Check cache first, fetch raw markdown if miss

## References

- [llmstxt.org](https://llmstxt.org/) - Official llms.txt specification
- [code.claude.com/docs/llms.txt](https://code.claude.com/docs/llms.txt) - Example manifest
- ADR-0005: Corpus Skill/Command Architecture - Source type structure
