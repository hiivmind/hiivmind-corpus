# Extension Consequences

Domain-specific consequences for corpus operations. These extensions can be replaced or augmented for different use cases.

---

## Overview

While [core consequences](../core/) provide fundamental workflow operations, extensions add domain-specific functionality:

| Extension | Purpose | Consequence Count |
|-----------|---------|-------------------|
| [file-system.md](file-system.md) | Corpus file operations | 5 |
| [config.md](config.md) | Config.yaml management | 3 |
| [git.md](git.md) | Git source operations | 4 |
| [web.md](web.md) | Web source operations | 2 |
| [discovery.md](discovery.md) | Corpus discovery | 1 |

---

## Quick Reference

| Consequence Type | File | Description |
|------------------|------|-------------|
| `read_config` | [file-system.md](file-system.md) | Read corpus config.yaml |
| `read_file` | [file-system.md](file-system.md) | Read arbitrary file |
| `write_file` | [file-system.md](file-system.md) | Write content to file |
| `create_directory` | [file-system.md](file-system.md) | Create directory |
| `delete_file` | [file-system.md](file-system.md) | Delete file |
| `write_config_entry` | [config.md](config.md) | Update config.yaml field |
| `add_source` | [config.md](config.md) | Add source to config |
| `update_source` | [config.md](config.md) | Update existing source |
| `clone_repo` | [git.md](git.md) | Clone git repository |
| `get_sha` | [git.md](git.md) | Get HEAD commit SHA |
| `git_pull` | [git.md](git.md) | Pull latest changes |
| `git_fetch` | [git.md](git.md) | Fetch remote refs |
| `web_fetch` | [web.md](web.md) | Fetch URL content |
| `cache_web_content` | [web.md](web.md) | Save fetched content |
| `discover_installed_corpora` | [discovery.md](discovery.md) | Scan for installed corpora |

---

## Design Philosophy

Extensions are designed to be:

1. **Replaceable** - Different domains may need different implementations
2. **Self-contained** - Each extension handles its own domain
3. **Composable** - Extensions work with core consequences
4. **Pattern-based** - Reference `lib/corpus/patterns/` for algorithms

---

## Adding New Extensions

To add a new extension domain:

1. **Create domain file** - `lib/workflow/consequences/extensions/{domain}.md`
2. **Follow template structure:**
   ```markdown
   # {Domain} Consequences

   Brief description of the domain.

   ---

   ## {consequence_type}

   Description.

   ```yaml
   - type: {consequence_type}
     param: value
   ```

   **Parameters:**
   | Name | Type | Required | Description |
   |------|------|----------|-------------|
   ...

   **Effect:**
   ```
   pseudocode
   ```

   ---

   ## Related Documentation

   - **Parent:** [README.md](README.md) - Extension overview
   - **Core:** [../core/](../core/) - Core consequences
   ...
   ```
3. **Update this README** - Add to tables above
4. **Update parent README** - `../README.md`

---

## Related Documentation

- **Parent:** [../README.md](../README.md) - Consequence taxonomy
- **Core consequences:** [../core/](../core/) - Fundamental workflow operations
- **Shared patterns:** [../core/shared.md](../core/shared.md) - Interpolation, parameters
- **Corpus patterns:** `lib/corpus/patterns/` - Algorithm documentation
