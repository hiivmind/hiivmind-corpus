# Batch Upgrade (Marketplaces)

For marketplaces with multiple corpora:

```bash
# From marketplace root
ls -d hiivmind-corpus-*/
```

## User Options

Offer these options:
1. **Upgrade all** - Apply same upgrades to all corpora
2. **Upgrade selected** - Choose which corpora to upgrade
3. **Report only** - Show what would change without applying

## Consolidated Batch Report

For batch upgrades, show consolidated report:

```
Batch Upgrade Report
════════════════════

hiivmind-corpus-polars:
  - Missing: project-awareness.md, 3 navigate sections

hiivmind-corpus-ibis:
  - Missing: project-awareness.md, 3 navigate sections

hiivmind-corpus-narwhals:
  - Missing: project-awareness.md, 3 navigate sections

Apply upgrades to all 3 corpora? [y/n]
```

---

## Example Session

**User**: "Upgrade my polars corpus"

**Step 1**: Locate - Found at current directory
**Step 2**: Detect - Standalone plugin type
**Step 3**: Compare:
- Navigate skill missing "Making Projects Aware" section
- No project-awareness.md file
**Step 4**: Report findings to user
**Step 5**: User confirms → Apply:
- Create references/project-awareness.md with Polars-specific content
- Append "Making Projects Aware" section to navigate skill
**Step 6**: Verify and show git status

---

## Version Tracking

When upgrades are applied, consider adding a version marker to config.yaml:

```yaml
# In data/config.yaml
corpus_version: "2025-12-13"  # Date of last upgrade
```

This helps track which corpora have been upgraded.
