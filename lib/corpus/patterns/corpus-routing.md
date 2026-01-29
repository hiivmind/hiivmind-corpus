# Pattern: Corpus Routing

## Purpose

Match user queries to the appropriate corpus based on keywords, context, and explicit naming.

## When to Use

- When a user asks a question that might relate to documentation
- When navigating without specifying which corpus
- When the gateway command receives arguments to route

## Routing Priority

1. **Explicit corpus name** - User specifies corpus: "search flyio for..."
2. **Keyword match** - Query contains corpus keywords
3. **Context match** - Current project has only one corpus registered
4. **Ambiguous** - Multiple matches, ask user to clarify

## Keyword Matching

### Load Keywords

For each registered corpus, extract keywords from `config.yaml`:

```yaml
corpus:
  keywords:
    - flyio
    - fly.io
    - deployment
    - hosting
```

### Match Algorithm

```python
def match_corpus(query: str, corpora: list) -> list[tuple[str, float]]:
    """Return list of (corpus_id, score) sorted by score descending."""
    query_lower = query.lower()
    matches = []

    for corpus in corpora:
        score = 0
        for keyword in corpus.keywords:
            if keyword.lower() in query_lower:
                # Exact word match scores higher
                if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower, re.I):
                    score += 10
                else:
                    score += 5

        if score > 0:
            matches.append((corpus.id, score))

    return sorted(matches, key=lambda x: x[1], reverse=True)
```

### Pseudocode Implementation

```
FOR each registered corpus:
    READ config.yaml from corpus source
    EXTRACT corpus.keywords[]

    FOR each keyword IN keywords:
        IF query contains keyword (case-insensitive):
            IF keyword is word-boundary match:
                score += 10
            ELSE (substring match):
                score += 5

    IF score > 0:
        ADD (corpus_id, score) to matches

SORT matches by score descending
RETURN matches
```

## Routing Outcomes

### Single Clear Winner

When one corpus scores significantly higher:

```
Query: "How do I deploy to fly.io?"
Matches:
  - flyio: 20 (matches "fly.io" + "deploy")
  - polars: 0

Action: Route directly to flyio corpus navigation
```

### Multiple Matches (Ambiguous)

When multiple corpora match with similar scores:

```
Query: "How do I read a CSV file?"
Matches:
  - polars: 10 (matches "read")
  - pandas: 10 (matches "CSV")

Action: Ask user to clarify which corpus
```

**Clarification prompt:**
```
Multiple corpora match your query:

1. **Polars** - DataFrame, lazy evaluation, expressions
2. **Pandas** - DataFrame, data analysis

Which would you like to search?
```

### No Matches

When no corpus keywords match:

```
Query: "What's the weather today?"
Matches: []

Action: Either search all corpora or inform user
```

**Response options:**
1. Search all registered corpora (if few)
2. List available corpora for user selection
3. Inform that no relevant corpus found

## Explicit Corpus Naming

Users can explicitly name a corpus to bypass keyword routing:

**Patterns recognized:**
```
"search flyio for deployment"           → corpus=flyio, query="deployment"
"flyio: how to deploy"                  → corpus=flyio, query="how to deploy"
"in the polars docs, what is..."        → corpus=polars
"/hiivmind-corpus navigate flyio ..."   → corpus=flyio (from command args)
```

**Extraction regex:**
```regex
(?:search\s+)?(\w+)(?:\s+for\s+|\s*:\s*)(.+)
(?:in\s+(?:the\s+)?)?(\w+)\s+(?:docs?|documentation|corpus)\s*[,:]?\s*(.+)
```

## Context-Aware Routing

### Single Corpus Context

When only one corpus is registered:

```yaml
# .hiivmind/corpus/registry.yaml
corpora:
  - id: flyio
    source: ...
```

Any documentation query routes to flyio without disambiguation.

### Project Type Detection

Use project context to prioritize corpora:

```
IF project has fly.toml:
    Boost flyio corpus score by 50%

IF project has pyproject.toml with polars dependency:
    Boost polars corpus score by 50%
```

## Implementation in Navigate Skill

```yaml
# In workflow.yaml
nodes:
  route_query:
    type: action
    actions:
      - type: reference
        doc: lib/corpus/patterns/corpus-routing.md
        section: "Match Algorithm"
      - type: compute
        expression: |
          // Load registry
          const registry = computed.registry;

          // Score each corpus
          const scores = [];
          for (const corpus of registry.corpora) {
            let score = 0;
            for (const keyword of corpus.keywords || []) {
              if (state.query.toLowerCase().includes(keyword.toLowerCase())) {
                score += 10;
              }
            }
            if (score > 0) {
              scores.push({ id: corpus.id, score });
            }
          }

          // Sort by score
          scores.sort((a, b) => b.score - a.score);
          return scores;
        store_as: computed.corpus_matches
      - type: evaluate
        expression: "computed.corpus_matches.length === 1"
        set_flag: has_single_match
    on_success: check_match_count

  check_match_count:
    type: conditional
    condition:
      type: flag_set
      flag: has_single_match
    branches:
      true: navigate_single_corpus
      false: check_for_ambiguous
```

## Error Handling

**No corpora registered:**
```
No documentation corpora are registered for this project.

Register a corpus with:
  /hiivmind-corpus register github:hiivmind/hiivmind-corpus-flyio

Or discover available corpora:
  /hiivmind-corpus discover
```

**Corpus keywords not loaded:**
```
Could not load keywords for corpus 'flyio'.
Attempting to fetch config from source...

If this persists, try:
  /hiivmind-corpus refresh flyio
```

## Related Patterns

- **Registry Loading:** `registry-loading.md` - Loading the registry
- **Index Fetching:** `index-fetching.md` - Fetching corpus content
- **Config Parsing:** `config-parsing.md` - Extracting keywords from config
