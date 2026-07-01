# Install hiivmind-corpus

This repository is a whole-plugin distribution. Install the repository root so platform loaders can see `skills/`, `commands/`, `agents/`, and `lib/`.

## Claude Code

```bash
claude plugin marketplace add hiivmind/hiivmind-corpus
claude plugin install hiivmind-corpus@hiivmind
```

Verify with `claude plugin list` and look for `hiivmind-corpus`.

## Codex

Register the GitHub repository as a marketplace source:

```bash
codex plugin marketplace add https://github.com/hiivmind/hiivmind-corpus
```

Then open `/plugins` in Codex and install `hiivmind-corpus`.

Verify in a fresh session that `hiivmind-corpus:*` skills are listed, or that `~/.codex/config.toml` contains enabled entries for the marketplace and plugin.

## Cursor

Install from the plugin source:

```text
/add-plugin hiivmind-corpus@https://github.com/hiivmind/hiivmind-corpus
```

For a local checkout, symlink or copy the repository into Cursor's local plugin directory and reload Cursor.

## Gemini CLI

Install from GitHub:

```bash
gemini extensions install https://github.com/hiivmind/hiivmind-corpus
```

For local development:

```bash
gemini extensions link /path/to/hiivmind-corpus
```

Verify with `gemini extensions list`.

## Antigravity

Use the repository as a plugin source, or copy the skill directories into an Antigravity project:

```bash
mkdir -p .agents/skills
cp -R /path/to/hiivmind-corpus/skills/* .agents/skills/
```

Verify that the `hiivmind-corpus-*` skills appear in a fresh Antigravity session.

## OpenClaw

Install a local clone:

```bash
git clone https://github.com/hiivmind/hiivmind-corpus
openclaw plugins install -l ./hiivmind-corpus
```

Or add the checkout path to `plugins.load.paths` in `~/.openclaw/openclaw.json`.

Verify with `openclaw plugins list`.
