#!/usr/bin/env bash
# render-index.sh — Deterministic index.yaml → index.md renderer
# Copied to corpus root during build. Used by build, refresh, and CI workflows.
#
# Usage: bash render-index.sh index.yaml
# Reads config.yaml from the same directory for corpus name and source count.
# Requires: yq 4.0+ (mikefarah/yq)

set -euo pipefail

INDEX_YAML="${1:?Usage: render-index.sh <path-to-index.yaml>}"
DIR=$(dirname "$INDEX_YAML")
CONFIG_YAML="${DIR}/config.yaml"

if [ ! -f "$INDEX_YAML" ]; then
  echo "Error: $INDEX_YAML not found" >&2
  exit 1
fi

if [ ! -f "$CONFIG_YAML" ]; then
  echo "Error: $CONFIG_YAML not found (needed for corpus name)" >&2
  exit 1
fi

# Read metadata
CORPUS_NAME=$(yq '.corpus.display_name // .corpus.name' "$CONFIG_YAML")
SOURCE_COUNT=$(yq '.sources | length' "$CONFIG_YAML")
ENTRY_COUNT=$(yq '.meta.entry_count' "$INDEX_YAML")
GENERATED_AT=$(yq '.meta.generated_at' "$INDEX_YAML")

OUTPUT="${DIR}/index.md"

# Get sorted unique categories
CATEGORIES=$(yq -r '.entries[].category' "$INDEX_YAML" | sort -u)

{
  # Header
  echo "# ${CORPUS_NAME} Documentation Index"
  echo ""
  echo "> Sources: ${SOURCE_COUNT} | Entries: ${ENTRY_COUNT} | Generated: ${GENERATED_AT}"
  echo '> Generated from `index.yaml` — do not edit directly'
  echo ""
  echo "---"

  # Entries grouped by category
  for CAT in $CATEGORIES; do
    echo ""
    # Title-case the category for heading
    CAT_HEADING=$(echo "$CAT" | sed 's/\b\(.\)/\u\1/g')
    echo "## ${CAT_HEADING}"
    echo ""

    # Entries in this category, sorted by title
    #
    # Uses yq for data extraction (TSV) and bash for formatting.
    # mikefarah/yq v4 does NOT support jq-style if/then/else, and passing
    # complex expressions via bash double-quoted strings with escaped inner
    # quotes (\") breaks yq's lexer. This approach avoids both issues:
    # - env() reads the loop variable without bash interpolation
    # - @tsv output lets bash handle conditional suffixes cleanly
    CAT_FILTER="$CAT" yq -r '
      .entries
      | map(select(.category == env(CAT_FILTER)))
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

  # Footer
  echo ""
  echo "---"
  echo ""
  echo "*Rendered from index.yaml at ${GENERATED_AT}*"
} > "$OUTPUT"

echo "Rendered ${OUTPUT} (${ENTRY_COUNT} entries)"
