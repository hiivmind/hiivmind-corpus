#!/usr/bin/env bash
# render-index.sh — Deterministic index.yaml → index.md renderer
# Copied to corpus root during build/migrate. Used by build, refresh, and CI.
#
# Usage: bash render-index.sh index.yaml
# Reads config.yaml from the same directory for corpus name, source count, and
# the render: block (strategy: single | tiered).
# Requires: yq 4.0+ (mikefarah/yq)

set -euo pipefail

INDEX_YAML="${1:?Usage: render-index.sh <path-to-index.yaml>}"
DIR=$(dirname "$INDEX_YAML")
CONFIG_YAML="${DIR}/config.yaml"

[ -f "$INDEX_YAML" ] || { echo "Error: $INDEX_YAML not found" >&2; exit 1; }
[ -f "$CONFIG_YAML" ] || { echo "Error: $CONFIG_YAML not found (needed for corpus name)" >&2; exit 1; }

CORPUS_NAME=$(yq '.corpus.display_name // .corpus.name' "$CONFIG_YAML")
SOURCE_COUNT=$(yq '.sources | length' "$CONFIG_YAML")
ENTRY_COUNT=$(yq '.meta.entry_count' "$INDEX_YAML")
GENERATED_AT=$(yq '.meta.generated_at' "$INDEX_YAML")
STRATEGY=$(yq '.render.strategy // "single"' "$CONFIG_YAML")

# Space-separated list of configured section ids, set by render_tiered.
# "main" mode falls back to entries whose .section is empty OR not in this list
# (so removing a section from config never loses its entries — they re-home to
# the main index on the next render).
VALID_SECTIONS=""

# Emit entry lines grouped by category (h2), for the subset selected by MODE:
#   MODE=all                  every entry
#   MODE=main                 unsectioned entries + orphans (section not in VALID)
#   MODE=section SECTION=<id> entries with .section == <id>
# Uses yq for extraction (TSV) and bash for formatting; mikefarah yq v4 has no
# jq-style if/then/else, and env() avoids all quote-escaping issues.
render_entries() {
  local mode="$1" section="${2:-}"
  local categories
  categories=$(MODE="$mode" SECTION="$section" VALID="$VALID_SECTIONS" yq -r '
    (strenv(VALID) | split(" ")) as $valid
    | .entries
    | map(select(
        (env(MODE) == "all")
        or (env(MODE) == "main" and (
             (.section // "") as $s | ($s == "" or ($valid | contains([$s]) | not))
           ))
        or (env(MODE) == "section" and (.section // "") == env(SECTION))
      ))
    | .[].category
  ' "$INDEX_YAML" | sort -u)

  for CAT in $categories; do
    echo ""
    CAT_HEADING=$(echo "$CAT" | sed 's/\b\(.\)/\u\1/g')
    echo "## ${CAT_HEADING}"
    echo ""
    MODE="$mode" SECTION="$section" VALID="$VALID_SECTIONS" CAT_FILTER="$CAT" yq -r '
      (strenv(VALID) | split(" ")) as $valid
      | .entries
      | map(select(
          ((env(MODE) == "all")
           or (env(MODE) == "main" and (
                (.section // "") as $s | ($s == "" or ($valid | contains([$s]) | not))
              ))
           or (env(MODE) == "section" and (.section // "") == env(SECTION)))
          and .category == env(CAT_FILTER)
        ))
      | sort_by(.title)
      | .[]
      | [.title, .id, .summary, .size, (.grep_hint // ""), (.stale | tostring)]
      | @tsv
    ' "$INDEX_YAML" | while IFS=$'\t' read -r title id summary size grep_hint stale; do
      line="- **${title}** \`${id}\` - ${summary}"
      if [[ "$size" == "large" && -n "$grep_hint" ]]; then
        line+=" ⚡ GREP - \`${grep_hint}\`"
      fi
      if [[ "$stale" == "true" ]]; then
        line+=" ⏳ STALE"
      fi
      echo "$line"
    done
  done
}

count_section_entries() {
  local section="$1"
  SECTION="$section" yq -r '[.entries[] | select((.section // "") == env(SECTION))] | length' "$INDEX_YAML"
}

render_single() {
  {
    echo "# ${CORPUS_NAME} Documentation Index"
    echo ""
    echo "> Sources: ${SOURCE_COUNT} | Entries: ${ENTRY_COUNT} | Generated: ${GENERATED_AT}"
    echo '> Generated from `index.yaml` — do not edit directly'
    echo ""
    echo "---"
    render_entries all
    echo ""
    echo "---"
    echo ""
    echo "*Rendered from index.yaml at ${GENERATED_AT}*"
  } > "${DIR}/index.md"
  echo "Rendered ${DIR}/index.md (${ENTRY_COUNT} entries)"
}

render_tiered() {
  local section_ids
  section_ids=$(yq -r '.render.sections[].id' "$CONFIG_YAML")
  # Space-separated form for the "main"-mode orphan fallback in render_entries.
  VALID_SECTIONS=$(echo $section_ids)

  # --- main index.md ---
  {
    echo "# ${CORPUS_NAME} Documentation Index"
    echo ""
    echo "> Sources: ${SOURCE_COUNT} | Entries: ${ENTRY_COUNT} | Generated: ${GENERATED_AT}"
    echo '> Generated from `index.yaml` — do not edit directly'
    echo ""
    echo "This corpus uses a **tiered index**. Start here, then drill into the"
    echo "sub-index files for detailed entries."
    echo ""
    echo "---"

    # Quick reference (pinned entry IDs, in config order)
    QR_COUNT=$(yq -r '.render.quick_reference // [] | length' "$CONFIG_YAML")
    if [[ "$QR_COUNT" -gt 0 ]]; then
      echo ""
      echo "## Quick Reference"
      echo ""
      yq -r '.render.quick_reference[]' "$CONFIG_YAML" | while read -r qid; do
        QID="$qid" yq -r '
          .entries[] | select(.id == env(QID))
          | [.title, .id, .summary] | @tsv
        ' "$INDEX_YAML" | while IFS=$'\t' read -r title id summary; do
          echo "- **${title}** \`${id}\` - ${summary}"
        done
      done
      echo ""
      echo "---"
    fi

    # Section summaries
    for SID in $section_ids; do
      S_TITLE=$(SID="$SID" yq -r '.render.sections[] | select(.id == env(SID)) | .title' "$CONFIG_YAML")
      S_DESC=$(SID="$SID" yq -r '.render.sections[] | select(.id == env(SID)) | .description // ""' "$CONFIG_YAML")
      N=$(count_section_entries "$SID")
      echo ""
      echo "## ${S_TITLE}"
      [[ -n "$S_DESC" ]] && { echo "*${S_DESC}*"; echo ""; }
      echo "→ See [index-${SID}.md](index-${SID}.md) for ${N} detailed entries"
      echo ""
      echo "---"
    done

    # Unsectioned entries (and orphans whose section is no longer defined) render inline
    MAIN_COUNT=$(VALID="$VALID_SECTIONS" yq -r '(strenv(VALID) | split(" ")) as $valid | [.entries[] | select((.section // "") as $s | ($s == "" or ($valid | contains([$s]) | not)))] | length' "$INDEX_YAML")
    if [[ "$MAIN_COUNT" -gt 0 ]]; then
      render_entries main
      echo ""
      echo "---"
    fi

    echo ""
    echo "*Rendered from index.yaml at ${GENERATED_AT}*"
  } > "${DIR}/index.md"

  # --- one sub-index per section ---
  for SID in $section_ids; do
    S_TITLE=$(SID="$SID" yq -r '.render.sections[] | select(.id == env(SID)) | .title' "$CONFIG_YAML")
    {
      echo "# ${CORPUS_NAME} — ${S_TITLE}"
      echo ""
      echo "> Part of the ${CORPUS_NAME} Documentation Index — back to [main index](index.md)"
      echo '> Generated from `index.yaml` — do not edit directly'
      echo ""
      echo "---"
      render_entries section "$SID"
      echo ""
      echo "---"
      echo ""
      echo "*Rendered from index.yaml at ${GENERATED_AT}*"
    } > "${DIR}/index-${SID}.md"
  done

  # Remove sub-indexes for sections no longer defined (rename/removal hygiene)
  for f in "${DIR}"/index-*.md; do
    [ -e "$f" ] || continue
    base=$(basename "$f" .md); sid="${base#index-}"
    echo "$section_ids" | grep -qx "$sid" || rm "$f"
  done

  echo "Rendered ${DIR}/index.md + $(echo "$section_ids" | wc -w | tr -d ' ') sub-indexes (${ENTRY_COUNT} entries)"
}

if [[ "$STRATEGY" == "tiered" ]]; then
  render_tiered
else
  render_single
fi
