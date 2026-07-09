# Pattern: Applying Source Changes to the Index

Single source of truth for how refresh flows (interactive and headless) apply
detected file changes (A/M/D) to the index. Both refresh skills reference
this pattern — do not duplicate these rules into skill files.

## Inputs

- `updated_sources`: per-source list of file changes with status A/M/D
  (relative paths under the source's `docs_root`)
- Index format: v2 (`index.yaml` present) or v1 (`index.md` only)
- Index structure: single or tiered (v1 with `index-*.md` sub-indexes)

## v2 format (index.yaml)

See also `index-format-v2.md` and `freshness.md`.

```pseudocode
UPDATE_INDEX_V2():
  index = parse_yaml(Read("index.yaml"))

  FOR EACH source IN computed.updated_sources:
    FOR EACH change IN source.files_changed:
      entry_id = source.id + ":" + relative_path(change.path, source.docs_root)

      SWITCH change.status:
        CASE "M":
          entry = find_entry(index, entry_id)
          IF entry:
            entry.stale = true
            entry.stale_since = now()
            # Preserve: summary, tags, keywords, concepts, links_from
            computed.index_changes.modified += 1
            computed.index_changes.stale_entries.append(entry_id)

        CASE "A":
          append_entry(index, {
            id: entry_id, source: source.id, path: relative_path,
            stale: true, stale_since: now(),
            category: "unknown", summary: "Pending re-scan",
            tags: [], keywords: [], concepts: []
          })
          computed.index_changes.added += 1
          computed.index_changes.stale_entries.append(entry_id)

        CASE "D":
          remove_entry(index, entry_id)
          remove_from_graph_if_referenced("graph.yaml", entry_id)
          computed.index_changes.removed += 1

  Update index.meta.generated_at and entry_count, save index.yaml
  Re-render: bash ./render-index.sh index.yaml (if render script exists)
```

Notes:
- `links_from` is NOT updated during refresh — recomputing cross-references
  requires a full build.
- `concepts` is preserved as-is — full concept remapping requires the graph
  skill's add-concept with updated entry selection.
- Stale entries are resolved by `hiivmind-corpus-enrich-headless` (headless
  pipelines) or the next build/LLM re-scan (interactive).

## v1 format (index.md, single or tiered)

Apply changes directly to `index.md`. If tiered (glob `index-*.md`), map
changes to affected sub-indexes and update each, then update the main
`index.md` summary section. See `sources/shared.md`.

Per-change rules:

- **D (deleted):** Remove the entry line from the relevant section file.
- **M (modified):** Path is unchanged — the entry reference remains valid. No section edit needed.
- **A (added):** Read the file from `.source/{id}/` and extract a real title and intro **before** writing the entry. Never write a directory summary or placeholder stub — v1 has no re-scan phase, so entries need real content from the start.

  ```pseudocode
  FOR EACH added_path IN source.files_changed WHERE status == "A":
    content = git_show(".source/{source.id}", "HEAD:{docs_root}/{relative_path}")
    title   = frontmatter.title OR frontmatter.shortTitle OR first_h1(content) OR filename_humanized
    intro   = frontmatter.intro (clean template vars, truncate to ~120 chars)
    entry   = "- **{title}** `{source.id}:{relative_path}`"
    IF intro: entry += " — {intro}"
    append entry to relevant section in index file
  ```

  Template variables (e.g. Liquid `{% data variables.X.Y %}`) must be resolved or stripped
  **before** truncating — truncating mid-tag leaves broken markup in the index.

  Place each entry in the appropriate existing `##` section based on path structure
  (e.g. `copilot/concepts/...` → `## Concepts`, `copilot/how-tos/...` → `## How-Tos`).
  Never stage entries under a temporary heading like "New in This Refresh" — the index
  is a durable source of truth, not a changelog.

### Tiered index (v1)

1. Map changes to affected sub-indexes (match source sections to `index-*.md` files)
2. For each affected sub-index: read `index-{section}.md`, apply relevant
   changes per the rules above, save
3. Update main `index.md` summary section

## Updating config.yaml after index changes (both formats)

After index changes are saved:

1. Update `index.last_updated_at` in config.yaml
2. For each updated source:
   - Set `last_commit_sha` (git/self/generated-docs)
   - Set `last_indexed_at` to current timestamp
   - Update `manifest.last_hash` (llms-txt)
3. Save config.yaml

## Embedding update (v2 with index-embeddings.lance/ present)

1. If `index-embeddings.lance/` does not exist: no action (refresh does not
   prompt for opt-in).
2. Otherwise run `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/detect.py`:
   - "ready" → `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/embed.py index.yaml index-embeddings.lance/`
     (incremental — only re-embeds entries with changed metadata text)
   - "no-model" → skip; never trigger a model download during refresh
   - "not-installed" → skip
3. Headless flows defer embedding entirely when stale entries exist — see
   `headless-contract.md` § "embeddings: deferred". Interactive flows may
   embed immediately because summaries are regenerated in-session.
