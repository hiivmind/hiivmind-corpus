# Pattern: Tool Detection

## Purpose

Establish available tool capabilities at the start of corpus operations, enabling runtime adaptation to the environment.

## When to Use

- At the start of any corpus skill that needs YAML parsing, git operations, or file search
- Once per session (cache results mentally for reuse)
- Before suggesting commands to the user

## Tool Capability Matrix

| Capability | Required For | Preferred | Alternatives | Fallback |
|------------|--------------|-----------|--------------|----------|
| YAML parsing | Config reading | yq | python+pyyaml | grep+sed |
| Git operations | Git sources | git | (none) | Web URLs only |
| File search | Doc discovery | Claude Glob/Grep | rg, grep | find |
| JSON parsing | (rare) | jq | python | grep |

## Tool Tiers

### Tier 1: Required (no alternative)

**git** - Required for git-based documentation sources. Cannot proceed without it for git operations.

### Tier 2: Strongly Recommended (degraded without)

**YAML parsing** (yq OR python+pyyaml) - Essential for reading config.yaml reliably. Grep-based fallback exists but is fragile and may fail on complex YAML structures (multi-line values, nested objects, special characters).

### Tier 3: Optional (Claude tools usually sufficient)

- **rg** (ripgrep) - Faster search for large codebases, but Claude's Grep tool works well
- **jq** - JSON parsing, rarely needed in corpus operations

## Detection Commands

### Detect YAML Parsing Capability

**Using bash:**
```bash
# Check for yq
command -v yq >/dev/null 2>&1 && echo "yq:$(yq --version 2>&1 | head -1)"

# Check for Python + PyYAML
command -v python3 >/dev/null 2>&1 && python3 -c "import yaml; print('pyyaml:available')" 2>/dev/null
```

**Using PowerShell:**
```powershell
# Check for yq
if (Get-Command yq -ErrorAction SilentlyContinue) { yq --version }

# Check for Python + PyYAML
python3 -c "import yaml; print('pyyaml:available')" 2>$null
```

**Using Claude tools:**
```
Bash: command -v yq && yq --version
```

### Detect Git Capability

**Using bash:**
```bash
command -v git >/dev/null 2>&1 && echo "git:$(git --version)"
```

**Using PowerShell:**
```powershell
if (Get-Command git -ErrorAction SilentlyContinue) { git --version }
```

### Detect Search Tools (Optional)

**Using bash:**
```bash
command -v rg >/dev/null 2>&1 && echo "rg:$(rg --version | head -1)"
command -v jq >/dev/null 2>&1 && echo "jq:$(jq --version)"
```

## Detection Strategy

### Detect-Once-Per-Session

1. At the start of a corpus operation, check for available tools
2. Store results mentally (don't repeat detection in same session)
3. Adapt all subsequent commands to use available tools
4. Warn user if critical tools are missing

### Decision Flow

```
┌─────────────────────────────────────────────────────────┐
│                  Start Corpus Operation                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                Check for git (if git sources)           │
└─────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
     git available              git not available
            │                           │
            │                           ▼
            │               ┌───────────────────────┐
            │               │ BLOCK: Cannot proceed │
            │               │ with git sources      │
            │               │ (show install help)   │
            │               └───────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│                Check for YAML parsing                    │
└─────────────────────────────────────────────────────────┘
                          │
     ┌────────────────────┼────────────────────┐
     │                    │                    │
     ▼                    ▼                    ▼
 yq available      python+pyyaml         neither
     │                available               │
     │                    │                   │
     ▼                    ▼                   ▼
Use yq commands   Use python commands   WARN: Using grep
                                       fallback (unreliable)
```

## Recommendation Messages

### Critical (blocks operation)

When git is required but not found:

```
Git is required for git-based documentation sources but wasn't found.

Install git:
- Linux (Debian/Ubuntu): sudo apt install git
- Linux (Fedora): sudo dnf install git
- macOS: xcode-select --install
- Windows: https://git-scm.com/downloads

Cannot proceed with git source operations without git.
```

### Strong (degraded experience)

When no YAML parser is found:

```
No YAML parsing tool found (yq or python+pyyaml).
Operations will use grep-based fallback which may be unreliable for complex YAML.

For best results, install one of:
- yq (recommended): https://github.com/mikefarah/yq#install
- Python PyYAML: pip install pyyaml

Proceeding with fallback method...
```

### Informational (no action needed)

```
Note: Using grep for file search (ripgrep not found).
This works fine but may be slower for large codebases.
```

## Version Compatibility Notes

### yq

- **yq 4.x** (Mike Farah's Go version): Current syntax documented here
- **yq 3.x**: Different syntax - avoid or upgrade
- **yq (Python version)**: Different project entirely - check with `yq --version`

Verify yq 4.x:
```bash
yq --version  # Should show: yq (https://github.com/mikefarah/yq/) version v4.x.x
```

### Python

- Python 3.6+ recommended
- PyYAML: `pip install pyyaml` or `pip3 install pyyaml`

## Cross-Platform Notes

| Aspect | Unix (Linux/macOS) | Windows |
|--------|-------------------|---------|
| Tool detection | `command -v {tool}` | `Get-Command {tool}` |
| Shell | bash, zsh | PowerShell, cmd |
| Path separator | `/` | `\` (PowerShell accepts `/`) |
| Home directory | `$HOME`, `~` | `$env:USERPROFILE` |
| Package manager | apt, brew, dnf | winget, choco, scoop |

## Examples

### Example 1: Beginning of a Corpus Operation

**User**: "refresh status"

**LLM detection process**:
1. Check if git is available (for git sources)
2. Check if yq or python+pyyaml is available (for config reading)
3. Adapt commands based on results

**If yq available:**
```bash
yq '.sources[0].last_commit_sha' data/config.yaml
```

**If python+pyyaml available:**
```bash
python3 -c "import yaml; print(yaml.safe_load(open('data/config.yaml'))['sources'][0].get('last_commit_sha', ''))"
```

**If neither (fallback):**
```bash
grep -A1 'last_commit_sha:' data/config.yaml | tail -1 | sed 's/.*: //' | tr -d '"'
```

### Example 2: User on Windows

**Detection output:**
```
git: git version 2.42.0.windows.1
yq: not found
python3: Python 3.11.0
pyyaml: available
```

**Adaptation**: Use Python for all YAML operations, PowerShell-compatible paths.

### Example 3: Minimal Environment

**Detection output:**
```
git: git version 2.39.0
yq: not found
python3: not found
```

**Response**:
```
No YAML parsing tool found (yq or python+pyyaml).

For reliable operation, please install one of:
- yq: https://github.com/mikefarah/yq#install
- Python + PyYAML: Install Python 3, then `pip install pyyaml`

I'll proceed using grep-based fallback, but results may be unreliable
for complex configuration files.
```

## Error Handling

### Tool Not Found

- Clearly state which tool is missing
- Provide installation instructions for user's platform (if detectable)
- Explain consequences (blocked vs degraded)
- Offer alternatives if available

### Tool Found But Wrong Version

- yq 3.x vs 4.x: Show version, explain incompatibility, suggest upgrade
- Detect via version output differences

### Tool Available But Fails

- Could be permissions, path issues, or broken installation
- Show actual error message
- Suggest reinstallation

## Related Patterns

- **config-parsing.md** - Uses tool detection to choose YAML extraction method
- **discovery.md** - Uses tool detection for YAML parsing
- **status.md** - Uses tool detection for YAML parsing and git operations
- **sources/git.md** - Requires git detection for clone operations
