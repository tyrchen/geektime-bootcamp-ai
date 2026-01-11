# Codex CLI Reference

Complete command reference for the OpenAI Codex CLI tool.

## Installation

```bash
# npm (recommended)
npm install -g @openai/codex

# Homebrew (macOS)
brew install --cask codex
```

## Authentication

```bash
# Interactive authentication (recommended)
codex
# Follow prompts to sign in with ChatGPT account

# API key authentication
export CODEX_API_KEY="your-api-key"
```

## Core Commands

### Interactive Mode

```bash
codex                          # Start interactive TUI
codex "initial prompt"         # Start with initial prompt
codex -i image.png "prompt"    # Attach image to prompt
```

### Non-Interactive Mode (exec)

```bash
codex exec "prompt"                    # Run single task
codex exec --full-auto "prompt"        # Allow file edits
codex exec -o output.md "prompt"       # Save output to file
codex exec --json "prompt"             # JSON output stream
```

### Session Management

```bash
codex resume                   # Session picker UI
codex resume --last            # Resume most recent session
codex resume <SESSION_ID>      # Resume specific session
codex exec resume <SESSION_ID> # Resume in exec mode
codex exec resume --last       # Resume last in exec mode
```

## Command Line Flags

### General Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--model` | `-m` | Select model (e.g., o3, gpt-5.1-codex-max) |
| `--ask-for-approval` | `-a` | Request approval before actions |
| `--cd` | | Specify working directory |
| `--add-dir` | | Add multiple project directories |
| `--image` | `-i` | Attach images (comma-separated) |

### Exec-Specific Flags

| Flag | Description |
|------|-------------|
| `--full-auto` | Allow file edits without confirmation |
| `--sandbox danger-full-access` | Allow edits and network commands |
| `--skip-git-repo-check` | Disable Git repository requirement |
| `-o, --output-last-message` | Specify output file |
| `--json` | Stream events as JSON Lines |
| `--output-schema` | Provide JSON Schema for structured output |

## Configuration

Configuration file: `~/.codex/config.toml`

### Approval Policies

```toml
# Options: "untrusted", "on-failure", "on-request", "never"
approval_policy = "untrusted"
```

- `untrusted`: Prompt before running commands not in trusted set
- `on-failure`: Notify only when command fails
- `on-request`: Model decides when to escalate
- `never`: Run commands without prompting

### Model Settings

```toml
# Model selection
model = "o3"

# Reasoning depth: minimal, low, medium, high, xhigh
model_reasoning_effort = "high"

# Reasoning summary: auto, concise, detailed, none
model_reasoning_summary = "auto"
```

### Sandbox Configuration

```toml
# Options: "read-only", "workspace-write", "danger-full-access"
sandbox_mode = "read-only"
```

- `read-only`: Default, blocks write/network access
- `workspace-write`: Allow writing in current workspace
- `danger-full-access`: Disable sandboxing (use with caution)

### Feature Flags

```toml
[features]
web_search_request = true
view_image_tool = true
skills = true
```

### UI Settings

```toml
[tui]
notifications = true

[history]
persistence = true
```

## JSON Output Events

When using `--json`, events are streamed as JSON Lines:

| Event Type | Description |
|------------|-------------|
| `thread.started` | Conversation thread initialized |
| `turn.started` | New turn began |
| `turn.completed` | Turn finished |
| `item.started` | Processing item |
| `item.updated` | Item progress update |
| `item.completed` | Item finished |
| `error` | Error occurred |

### Parsing JSON Output

```bash
# Extract final message content
codex exec --json "prompt" 2>/dev/null | jq 'select(.type == "item.completed") | .item.content'

# Filter for specific event types
codex exec --json "prompt" 2>/dev/null | jq 'select(.type == "turn.completed")'
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CODEX_API_KEY` | Override authentication |
| `CODEX_HOME` | Custom config directory |

## Interactive Shortcuts

| Shortcut | Action |
|----------|--------|
| `@` | Fuzzy filename search |
| `Esc-Esc` | Edit previous message |
| `Ctrl+V` / `Cmd+V` | Paste image |

## Shell Completion

```bash
# Generate completion scripts
codex completion bash >> ~/.bashrc
codex completion zsh >> ~/.zshrc
codex completion fish >> ~/.config/fish/completions/codex.fish
```

## Prompts Directory

Custom prompts can be stored in `~/.codex/prompts/`:

```markdown
<!-- ~/.codex/prompts/review.md -->
---
description: Review code with specific focus
argument-hint: FILE=<path> [FOCUS=<section>]
---

Review the code in $FILE. Pay special attention to $FOCUS.
```

Invoke with: `/prompts:review FILE=src/main.ts FOCUS="error handling"`

## Troubleshooting

### Common Issues

**Permission denied:**
```bash
# Re-authenticate
rm -rf ~/.codex/credentials*
codex
```

**Sandbox blocking operations:**
```bash
# Use workspace-write for file edits
codex exec --sandbox workspace-write "prompt"
```

**Git repository required:**
```bash
# Skip check for non-repo directories
codex exec --skip-git-repo-check "prompt"
```

**Timeout on long operations:**
```bash
# Use full-auto for extended tasks
codex exec --full-auto "prompt"
```
