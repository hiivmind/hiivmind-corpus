# Wave 3: Scheduler Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the seven copy-pasted scheduler tasks into one shared template + seven thin stubs, upstream the sparse-checkout/compare-API lesson into the plugin's `git.md` pattern, add branch/PR hygiene, and delete the redundant per-task pyprojects.

**Architecture:** Chosen model (user decision 2026-07-09): **shared template + thin stubs** — each `corpus-refresh-{name}/SKILL.md` shrinks to frontmatter + a 3-value Constants block + a pointer to `TEMPLATE-corpus-refresh.md` at the scheduler repo root. Directory names are preserved so the existing `~/.claude/scheduled-tasks/` symlinks and per-corpus schedules keep working untouched. The template gains branch/PR hygiene (detect superseded `automated/*` PRs, close them after the new PR lands, report unmerged-PR age). The hard-won git constraint moves into the plugin's `lib/corpus/patterns/sources/git.md`; the template keeps a one-line pointer.

**Tech Stack:** Markdown skill files only (no Python). Verification is structural: `diff`, `grep`, symlink resolution.

## Global Constraints

- Two repos, two branches, two PRs:
  - Plugin repo `/Users/nathanielramm/git/hiivmind/hiivmind-corpus` → branch `feature/wave3-git-sparse-checkout`
  - Scheduler repo `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler` → branch `feature/wave3-consolidate-template` (scheduler origin enforces "changes via PR"; local main was pushed to origin at c5eadf1 before this plan)
- Task directory names (`corpus-refresh-atproto` … `corpus-refresh-lancedb`) must NOT change — symlinks in `~/.claude/scheduled-tasks/` point at them by name.
- The template must be referenced by **absolute path** (`/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler/TEMPLATE-corpus-refresh.md`) — the routines runtime may read stubs through the symlink, where a relative `..` would resolve to `~/.claude/scheduled-tasks/`.
- `archive/` in the scheduler repo is untouched (including its pyproject.toml).
- Commit messages: conventional commits, ending with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- No force-push. PR bodies end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Acceptance (from backlog 05): adding a corpus = one stub file; a process change edits exactly one file (the template); `git.md` documents the compare-API limitation.

---

### Task 1: Upstream the git constraint into the plugin (`git.md` + refresh-headless pointer)

**Files:**
- Modify: `lib/corpus/patterns/sources/git.md` (insert new section after "Compare Clone to Indexed SHA", i.e. after the `**Return values:**` list around line 261, before `### Extraction Support`)
- Modify: `skills/hiivmind-corpus-refresh-headless/SKILL.md:100-115` (Phase 3 "Git source update")
- Modify: `docs/backlog/index.md` (item 05 status)

**Interfaces:**
- Produces: a `### Sparse Checkout for Large Repositories (and the compare-API prohibition)` heading in `git.md` that Task 2's template pointer cites by name.

- [ ] **Step 1: Create the plugin branch**

```bash
cd /Users/nathanielramm/git/hiivmind/hiivmind-corpus
git checkout main && git pull
git checkout -b feature/wave3-git-sparse-checkout
```

- [ ] **Step 2: Add the sparse-checkout section to git.md**

In `lib/corpus/patterns/sources/git.md`, immediately after the "Compare Clone to Indexed SHA" section's `**Return values:**` list (and the `---` separators that follow it, ~line 263), insert:

```markdown
### Sparse Checkout for Large Repositories (and the compare-API prohibition)

For large upstream repos — or whenever only `docs_root` matters — use a sparse,
blob-filtered clone instead of a full one. The clone lives in `.source/{id}/`
(gitignored) and persists between runs, so the clone cost is paid once;
subsequent runs just fetch and diff locally.

**Using bash:**
```bash
# First run — sparse clone of docs_root only
git clone --filter=blob:none --sparse --depth=50 <repo_url> .source/<id>
git -C .source/<id> sparse-checkout set <docs_root>
git -C .source/<id> checkout <branch>

# Subsequent runs — fetch and diff locally
git -C .source/<id> fetch --depth=50 origin <branch>
git -C .source/<id> diff --name-status <last_commit_sha>..FETCH_HEAD -- <docs_root>
```

**Never use the GitHub compare API**
(`gh api repos/{owner}/{repo}/compare/{base}...{head}`) **for change
detection.** It caps the returned file list at 300 entries and silently drops
the rest — a large documentation refresh will miss changed files with no error
or warning. This is an operational lesson learned in production (scheduled
corpus refreshes): always diff locally inside the clone.

---
```

(Keep the surrounding `---` separators balanced: one `---` before `### Extraction Support` must remain.)

- [ ] **Step 3: Add the pointer in refresh-headless Phase 3**

In `skills/hiivmind-corpus-refresh-headless/SKILL.md`, the "Git source update" subsection currently reads:

```markdown
Clone to `.source/{id}` if not present (depth 50). Then ensure the tracked SHA is
reachable for diffing:
```

Replace with:

```markdown
Clone to `.source/{id}` if not present (depth 50; for large repos prefer the
sparse blob-filtered clone — see "Sparse Checkout for Large Repositories" in
`patterns/sources/git.md`). Never use the GitHub compare API to list changed
files: it caps at 300 files and silently truncates. Then ensure the tracked
SHA is reachable for diffing:
```

- [ ] **Step 4: Flip backlog 05 status**

In `docs/backlog/index.md`, change item 05's Status cell from `Proposed` to `In progress (wave 3)`.

- [ ] **Step 5: Verify**

```bash
grep -n "compare API\|compare-API\|Sparse Checkout" lib/corpus/patterns/sources/git.md skills/hiivmind-corpus-refresh-headless/SKILL.md
```

Expected: the new section heading in git.md, the prohibition text in both files.

- [ ] **Step 6: Commit, push, PR**

```bash
git add lib/corpus/patterns/sources/git.md skills/hiivmind-corpus-refresh-headless/SKILL.md docs/backlog/index.md
git commit -m "docs(patterns): upstream sparse-checkout recipe and compare-API prohibition into git.md

The 300-file silent-truncation limit of the GitHub compare API was a
hard-won scheduler lesson living only in scheduler task files. Document
it where all refresh consumers can see it.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git push -u origin feature/wave3-git-sparse-checkout
gh pr create --title "docs(patterns): sparse-checkout recipe + compare-API prohibition in git.md" --body "$(cat <<'EOF'
Part of backlog item 05 (scheduler consolidation, wave 3).

- New git.md section: sparse blob-filtered clone recipe for large repos, persisted in .source/{id}/
- Documents the GitHub compare API's 300-file silent-truncation limit and prohibits it for change detection (previously this lesson lived only in scheduler task files)
- refresh-headless Phase 3 points at the new section
- Backlog 05 → In progress

Companion PR in hiivmind-corpus-scheduler consolidates the seven tasks into a shared template.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

### Task 2: Create `TEMPLATE-corpus-refresh.md` in the scheduler repo

**Files:**
- Create: `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler/TEMPLATE-corpus-refresh.md`

**Interfaces:**
- Consumes: the `git.md` section heading from Task 1 (pointer only — no hard dependency at runtime).
- Produces: the template file whose absolute path Task 3's stubs reference. State keys used by later phases: `computed.stale_branches` (list of `{branch, pr_number, pr_age_days}`), `computed.superseded_prs` (list of closed PR numbers).

- [ ] **Step 1: Create the scheduler branch**

```bash
cd /Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler
git checkout main && git pull
git checkout -b feature/wave3-consolidate-template
```

- [ ] **Step 2: Create the template from the lancedb task**

```bash
cp corpus-refresh-lancedb/SKILL.md TEMPLATE-corpus-refresh.md
```

Then apply the following exact edits to `TEMPLATE-corpus-refresh.md`:

**Edit 2a — replace the frontmatter and intro** (lines 1–15, everything up to and including the first `---` separator after the blockquote):

Old:
```markdown
---
name: corpus-refresh-lancedb
description: >
---

# Corpus Refresh — Scheduled Task

Automated refresh of a corpus repository. Delegates the actual refresh work to the headless
refresh skill, then handles branching, committing, and PR creation.

No user present — act autonomously, note judgment calls, end with `<run-summary>`.

> **To schedule a new corpus:** copy this skill directory, change only the Constants block
> below, and symlink into `~/.claude/scheduled-tasks/`. Everything else is derived.
```

New:
```markdown
# Corpus Refresh — Shared Task Template

Automated refresh of a corpus repository. Delegates the actual refresh work to the headless
refresh skill, then handles branching, committing, and PR creation.

No user present — act autonomously, note judgment calls, end with `<run-summary>`.

> **This is not a runnable task.** It is the single source of truth executed by the thin
> per-corpus stubs (`corpus-refresh-*/SKILL.md`), which supply the Constants. To schedule
> a new corpus: create a stub directory with a SKILL.md containing only frontmatter, a
> Constants block, and a pointer to this file, then symlink it into
> `~/.claude/scheduled-tasks/`. A process change edits this file only — never the stubs.
```

**Edit 2b — replace the Constants section:**

Old:
```markdown
## Constants

```yaml
CORPUS_PATH: /Users/nathanielramm/git/hiivmind/hiivmind-corpus-lancedb
CORPUS_REPO: hiivmind/hiivmind-corpus-lancedb
BRANCH_PREFIX: automated/corpus-refresh-lancedb
```
```

New:
```markdown
## Constants

Provided by the invoking stub's Constants block:

```yaml
CORPUS_PATH: # absolute path to the local corpus clone
CORPUS_REPO: # owner/name on GitHub
BRANCH_PREFIX: # e.g. automated/corpus-refresh-{name}
```
```

**Edit 2c — update State** (add hygiene keys; `stale_branch` becomes a list):

Old:
```yaml
  branch_name: null
  stale_branch: null
```

New:
```yaml
  branch_name: null
  stale_branches: []           # [{branch, pr_number, pr_age_days}] — unmerged automated/* branches
  superseded_prs: []           # PR numbers closed as superseded by this run's PR
```

**Edit 2d — replace the sparse-checkout blockquote in Phase 3** (the 17-line `> **Git source constraint:** …` block including its fenced bash example):

New (single short block in its place):
```markdown
> **Git source constraint:** follow the sparse-checkout recipe in the plugin's
> `lib/corpus/patterns/sources/git.md` ("Sparse Checkout for Large Repositories").
> Never use the GitHub compare API for change detection — it caps at 300 files and
> silently drops the rest. Clone sparse into `.source/<id>/` (persists between runs,
> gitignored) and use local `git diff`.
```

**Edit 2e — replace the stale-branch paragraph in Phase 2:**

Old:
```markdown
Check for existing branches matching `BRANCH_PREFIX*`. If any have unmerged commits,
log them for the summary but proceed with a fresh branch.
```

New:
````markdown
Detect leftover automated branches and their PRs:

```pseudocode
STALE_BRANCHES():
  branches = Bash("git branch -r --list 'origin/" + BRANCH_PREFIX + "*'")
  FOR b IN branches:
    pr = Bash("gh pr list --repo " + CORPUS_REPO + " --head " + strip_origin(b)
              + " --state open --json number,createdAt")
    IF pr not empty:
      computed.stale_branches += { branch: strip_origin(b),
                                   pr_number: pr[0].number,
                                   pr_age_days: days_between(pr[0].createdAt, now()) }
    ELSE IF b has commits not on main:
      computed.stale_branches += { branch: strip_origin(b), pr_number: null, pr_age_days: null }
```

Proceed with a fresh branch regardless — superseded PRs are closed in Phase 4
*after* the new PR exists, never before.
````

**Edit 2f — add supersede handling at the end of Phase 4** (after the `gh pr create` line, before the `---` separator):

```markdown
After the new PR is created successfully, close superseded automated PRs — each open
PR recorded in `computed.stale_branches` was generated by an earlier run from an older
upstream state, and this run's PR (regenerated from current main and current upstream)
replaces it:

```pseudocode
SUPERSEDE():
  FOR s IN computed.stale_branches WHERE s.pr_number != null:
    Bash("gh pr close " + s.pr_number + " --repo " + CORPUS_REPO
         + " --comment 'Superseded by " + computed.pr_url + " (regenerated from current upstream).'"
         + " --delete-branch")
    computed.superseded_prs += s.pr_number
```

If this run creates no PR (no changes), leave existing PRs open — they still carry
unmerged work — and only report their age in the summary.
```

**Edit 2g — extend SUMMARY:**

Old:
```markdown
Always reached. Report: sources checked/updated, index change counts, embedding status,
PR URL or "already current", any stale branches noted, any errors.
```

New:
```markdown
Always reached. Report: sources checked/updated, index change counts, embedding status,
PR URL or "already current", superseded PRs closed (numbers), and for any automated PR
left open its age in days (e.g. `stale automated PR: #12 (9 days old)`), any errors.
```

**Edit 2h — update the State Flow diagram footer**: in the `Phase 2` column of the State Flow table at the bottom, change `.stale_branch` to `.stale_branches`, and add `.superseded_prs` under the `Phase 4` column.

- [ ] **Step 3: Verify the template**

```bash
grep -c "corpus-refresh-lancedb\|hiivmind-corpus-lancedb" TEMPLATE-corpus-refresh.md
```

Expected: `0` (no corpus-specific residue).

```bash
grep -n "stale_branches\|superseded_prs\|Sparse Checkout" TEMPLATE-corpus-refresh.md
```

Expected: hits in State, Phase 2, Phase 4, SUMMARY, and the Phase 3 pointer.

- [ ] **Step 4: Commit**

```bash
git add TEMPLATE-corpus-refresh.md
git commit -m "feat: shared corpus-refresh template with branch/PR hygiene

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Rewrite the seven task SKILL.md files as thin stubs

**Files:**
- Modify (full rewrite): `corpus-refresh-atproto/SKILL.md`, `corpus-refresh-data/SKILL.md`, `corpus-refresh-fastmail/SKILL.md`, `corpus-refresh-flyio/SKILL.md`, `corpus-refresh-frictionless/SKILL.md`, `corpus-refresh-github/SKILL.md`, `corpus-refresh-lancedb/SKILL.md`

**Interfaces:**
- Consumes: `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler/TEMPLATE-corpus-refresh.md` (Task 2).
- Produces: seven stubs differing only in the `{name}` substitution.

- [ ] **Step 1: Write each stub**

Exact content, with `{name}` ∈ {atproto, data, fastmail, flyio, frictionless, github, lancedb}:

```markdown
---
name: corpus-refresh-{name}
description: Scheduled refresh of the {name} corpus — delegates to the shared corpus-refresh template
---

# Corpus Refresh — {name}

## Constants

```yaml
CORPUS_PATH: /Users/nathanielramm/git/hiivmind/hiivmind-corpus-{name}
CORPUS_REPO: hiivmind/hiivmind-corpus-{name}
BRANCH_PREFIX: automated/corpus-refresh-{name}
```

## Task

Read and execute the shared template with the Constants above:

`/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler/TEMPLATE-corpus-refresh.md`

Every phase, constraint, and output contract is defined there. Do not deviate
from it and do not improvise steps that are not in the template.
```

Write it with a loop to guarantee uniformity:

```bash
for name in atproto data fastmail flyio frictionless github lancedb; do
cat > corpus-refresh-$name/SKILL.md <<EOF
---
name: corpus-refresh-$name
description: Scheduled refresh of the $name corpus — delegates to the shared corpus-refresh template
---

# Corpus Refresh — $name

## Constants

\`\`\`yaml
CORPUS_PATH: /Users/nathanielramm/git/hiivmind/hiivmind-corpus-$name
CORPUS_REPO: hiivmind/hiivmind-corpus-$name
BRANCH_PREFIX: automated/corpus-refresh-$name
\`\`\`

## Task

Read and execute the shared template with the Constants above:

\`/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler/TEMPLATE-corpus-refresh.md\`

Every phase, constraint, and output contract is defined there. Do not deviate
from it and do not improvise steps that are not in the template.
EOF
done
```

- [ ] **Step 2: Verify uniformity and symlink integrity**

```bash
for t in atproto data fastmail flyio frictionless github; do
  diff <(sed "s/$t/NAME/g" corpus-refresh-$t/SKILL.md) <(sed 's/lancedb/NAME/g' corpus-refresh-lancedb/SKILL.md)
done
```

Expected: no output (stubs identical modulo name).

```bash
ls -la ~/.claude/scheduled-tasks/ && cat ~/.claude/scheduled-tasks/corpus-refresh-lancedb/SKILL.md | head -4
```

Expected: all seven symlinks still resolve; the stub content is served through the symlink.

- [ ] **Step 3: Commit**

```bash
git add corpus-refresh-*/SKILL.md
git commit -m "refactor: replace seven copied task bodies with thin stubs over the shared template

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Delete per-task pyprojects and update scheduler CLAUDE.md

**Files:**
- Delete: `corpus-refresh-{atproto,data,fastmail,flyio,frictionless,github,lancedb}/pyproject.toml`
- Modify: `/Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler/CLAUDE.md` (full rewrite of Structure, Common tasks, Dependencies sections)

**Interfaces:**
- Consumes: PEP 723 script metadata shipped in plugin PR #47 (`uv run` resolves script deps; per-task venvs unnecessary).

- [ ] **Step 1: Delete the pyprojects (archive untouched)**

```bash
git rm corpus-refresh-*/pyproject.toml
ls corpus-refresh-*/          # expected: SKILL.md only, in each
ls archive/templates/corpus-refresh/   # expected: pyproject.toml still present
```

- [ ] **Step 2: Rewrite CLAUDE.md**

Replace the full contents of `CLAUDE.md` with:

```markdown
# hiivmind-corpus-scheduler

Repository of scheduled tasks for automated corpus maintenance. Each subdirectory is a
self-contained Claude Code Routine that gets symlinked into `~/.claude/scheduled-tasks/`.

## Structure

```
TEMPLATE-corpus-refresh.md   # the single task definition: all phases, constraints, output contract
corpus-refresh-{name}/       # one thin stub per corpus
  SKILL.md                   # frontmatter + Constants (3 values) + pointer to the template
```

All process logic lives in `TEMPLATE-corpus-refresh.md`. Stubs supply only
`CORPUS_PATH`, `CORPUS_REPO`, and `BRANCH_PREFIX`.

## Deployment

Tasks are symlinked from this repo into the routines directory:

```bash
ln -s /Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler/{task-name} \
      ~/.claude/scheduled-tasks/{task-name}
```

Never copy files into `~/.claude/scheduled-tasks/` — always symlink so changes in
this repo propagate automatically.

## Dependencies

No per-task pyprojects. The plugin's Python scripts carry PEP 723 inline metadata and
are invoked with `uv run ${CLAUDE_PLUGIN_ROOT}/lib/corpus/scripts/<script>.py` — uv
resolves each script's dependencies into a cached ephemeral environment.

The fastembed model cache at `~/.cache/fastembed/` must be accessible to the routine
runtime. The model (`BAAI/bge-small-en-v1.5`, ~45MB) is downloaded on first use;
tasks skip embedding if the model isn't already cached.

## Common tasks

- **Add a new corpus refresh:** create `corpus-refresh-{name}/SKILL.md` by copying any
  existing stub and substituting the corpus name (three Constants + frontmatter), then
  symlink into `~/.claude/scheduled-tasks/`. Nothing else.
- **Change the refresh process:** edit `TEMPLATE-corpus-refresh.md` only. Stubs never
  change.
- **Update the headless refresh logic:** edit
  `hiivmind-corpus/skills/hiivmind-corpus-refresh-headless/SKILL.md` — the template
  delegates to it via CALL_SKILL. The template reads `refresh-result.yaml` /
  `enrich-result.yaml` result files from the corpus root and validates them with
  `validate_result.py` (see the plugin's `patterns/headless-contract.md`); the
  refresh → enrich-headless sequence is mandatory when stale entries exist.
- **Git source operations:** the sparse-checkout recipe and the GitHub compare-API
  prohibition are documented in the plugin's `lib/corpus/patterns/sources/git.md`.

## Related repos

- `hiivmind/hiivmind-corpus` — the corpus plugin containing the headless refresh skill
  and all pattern documentation referenced by the template
- `hiivmind/hiivmind-corpus-{name}` — individual corpus repositories that these tasks
  refresh
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: drop per-task pyprojects (PEP 723 scripts) and document template model in CLAUDE.md

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Finish the scheduler branch — final verification, push, PR

**Files:** none new.

- [ ] **Step 1: Acceptance checks (backlog 05)**

```bash
cd /Users/nathanielramm/git/hiivmind/hiivmind-corpus-scheduler
# a process change edits exactly one file:
ls TEMPLATE-corpus-refresh.md
# adding a corpus is a single stub:
wc -l corpus-refresh-*/SKILL.md          # expected: ~26 lines each, identical counts
# no per-task pyprojects remain outside archive/:
find . -name pyproject.toml -not -path './.git/*' -not -path './archive/*'   # expected: empty
# hygiene present:
grep -n "superseded_prs\|pr_age_days" TEMPLATE-corpus-refresh.md   # expected: hits
```

- [ ] **Step 2: Push and create PR**

```bash
git push -u origin feature/wave3-consolidate-template
gh pr create --title "refactor: consolidate seven tasks into shared template + stubs, add PR hygiene" --body "$(cat <<'EOF'
Implements backlog item 05 (scheduler consolidation) from hiivmind-corpus docs/backlog/05-scheduler-consolidation.md.

- All phases live in TEMPLATE-corpus-refresh.md; the seven tasks are now 3-constant stubs (directory names unchanged, so existing symlinks/schedules keep working)
- Branch/PR hygiene: superseded automated/* PRs are closed (with comment + branch delete) after the new PR lands; unmerged-PR age reported in <run-summary>
- Sparse-checkout/compare-API guidance upstreamed to the plugin's patterns/sources/git.md (companion PR in hiivmind-corpus); template keeps a pointer
- Per-task pyprojects deleted (plugin scripts are PEP 723 self-contained since hiivmind-corpus PR #47)
- CLAUDE.md updated: add-a-corpus = one stub; process change = edit the template only

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Report both PR URLs and stop**

After both PRs are open, report: plugin PR (git.md), scheduler PR (consolidation), and the note that backlog 05 flips to Done after both merge. Do not merge; the user merges.

---

## Post-merge follow-up (not part of this plan's branches)

- After both PRs merge: update `docs/backlog/index.md` item 05 → `Done (PR #N)` on plugin main.
- No symlink changes needed on the host — directory names were preserved.
