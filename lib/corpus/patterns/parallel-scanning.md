# Parallel Scanning Pattern

Use the `source-scanner` agent to parallelize operations across multiple sources in a corpus.

## When to Use

| Source Count | Approach | Reason |
|--------------|----------|--------|
| 1 source | Scan directly | No agent overhead |
| 2+ sources | Use source-scanner agent | Parallel execution |

**Decision rule:** Only spawn agents when there are multiple sources. Single-source corpora should scan directly using the source-specific patterns.

## Agent Invocation Mechanics

### Basic Pattern

1. For each source in config, spawn a `source-scanner` agent with:
   - Source ID, type, and configuration
   - Corpus root path
   - Context-specific instructions (build vs refresh)
2. Launch all agents in parallel (single message with multiple Task tool calls)
3. Collect results from each agent
4. Aggregate into combined summary/report

### Task Tool Invocation

```
Task tool with subagent_type="source-scanner":
  prompt: "[Context-specific prompt - see below]"
```

**Single message, multiple calls:** To achieve parallelism, include all Task tool calls in a single response message. The agent runtime will execute them concurrently.

## Performance Expectations

| Sources | Sequential | With Agents | Improvement |
|---------|-----------|-------------|-------------|
| 1 | Baseline | No change | - |
| 2 | 2x time | ~1.2x time | ~40% faster |
| 3 | 3x time | ~1.3x time | ~55% faster |
| 4+ | 4x+ time | ~1.5x time | ~60%+ faster |

Note: Actual speedup depends on source sizes and I/O characteristics.

## Context-Specific Prompts

### For Building (hiivmind-corpus-build)

```
Task tool with subagent_type="source-scanner":
  prompt: "Scan source '{source_id}' (type: {type}) at corpus path '{corpus_path}'.
           Config: repo_url={repo_url}, docs_root={docs_root}

           Return YAML with:
           - file_count: total doc files found
           - sections: array of top-level directories/categories
           - framework: detected doc framework (docusaurus, mkdocs, etc.)
           - large_files: files over 1000 lines (candidates for GREP markers)"
```

**Expected output format:**
```yaml
source_id: react
file_count: 150
sections:
  - learn
  - reference
  - community
framework: docusaurus
large_files:
  - reference/api/ReactDOM.md
```

### For Status Checking (hiivmind-corpus-refresh)

```
Task tool with subagent_type="source-scanner":
  prompt: "Check status for source '{source_id}' (type: {type}).
           Last indexed SHA: {last_commit_sha}
           Last indexed at: {last_indexed_at}

           Return YAML with:
           - source_id: the source identifier
           - status: CURRENT | UPDATES_AVAILABLE | ERROR
           - current_sha: (git only) current HEAD
           - commits_behind: (git only) number of commits since last index
           - changed_files: (git/local) list of modified files
           - error: (if status is ERROR) description"
```

**Expected output format:**
```yaml
source_id: react
status: UPDATES_AVAILABLE
current_sha: def456789
commits_behind: 47
changed_files:
  - reference/hooks.md
  - learn/thinking-in-react.md
```

## Aggregating Results

After collecting results from all agents:

### For Build

1. Sum file counts across sources
2. Merge section lists (prefix with source_id for disambiguation)
3. Compile list of all detected frameworks
4. Combine large_files lists with source prefixes

**Combined summary format:**
```
Found 3 sources:

1. react (git): 150 doc files
   Location: .source/react/src/content/
   Sections: learn, reference, community

2. team-standards (local): 5 files
   Location: data/uploads/team-standards/

3. kent-blog (web): 3 cached articles
   Location: .cache/web/kent-blog/

Total: 158 doc files across 3 sources
```

### For Status

1. Count sources by status (CURRENT vs UPDATES_AVAILABLE)
2. Calculate total changed files
3. List affected sections/sub-indexes

**Combined status format:**
```
Source Status:

1. react (git)
   - Status: UPDATES AVAILABLE (47 commits behind)
   - Changed files: 12

2. team-standards (local)
   - Status: UPDATES AVAILABLE (2 files modified)

3. kent-blog (web)
   - Status: CURRENT (cached 2 days ago)

Summary: 2 of 3 sources have updates available
```

## Error Handling

If an agent fails or times out:
- Report the error for that source
- Continue processing results from other agents
- Present partial results with clear indication of failures

```
Source Status:

1. react (git) - UPDATES AVAILABLE
2. team-standards (local) - ERROR: Directory not found
3. kent-blog (web) - CURRENT

⚠️ 1 source failed to check - see errors above
```

## Related

- **Agent definition:** `agents/source-scanner.md`
- **Source operations:** `lib/corpus/patterns/sources.md`
- **File discovery:** `lib/corpus/patterns/scanning.md`
- **Status checking:** `lib/corpus/patterns/status.md`
