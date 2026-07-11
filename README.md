# Wasabi

<p align="center">
  <img src="static/Wasabi-Header.png" width="1100" alt="Wasabi Logo">
</p>

## Overview

this documented is enhanced with ChatGPT.
read original messy progress journal (here)[./progress.md]

Wasabi is a Python-first terminal coding agent built as an engineering project to understand **secure and controlled agent execution**.

The project explores two main questions:

1. **How do you give an AI agent useful execution capabilities without giving it uncontrolled access to the system?**
2. **What tools and context mechanisms make a coding agent efficient enough to be practically useful instead of wasting tokens, time, and API cost?**

Wasabi gives an LLM access to a real software repository through a constrained set of tools for filesystem operations, Git, dependency management, search, and code execution. Sensitive operations are protected through explicit user permissions and executor-level security boundaries.

The second focus is efficiency. Instead of repeatedly reading entire files or loading a complete repository into context, Wasabi provides tools for fast search, precise reads, surgical edits, persistent project context, structural code understanding, diagnostics, and context compaction.

The project is primarily an exploration of the systems engineering behind coding agents: **how capabilities are exposed, how execution is controlled, how security boundaries are enforced, and how an agent can gather only the context necessary to perform useful work.**

---

## Core Areas

### Controlled Agent Execution

Wasabi does not give the model unrestricted shell or filesystem access. Instead, capabilities are exposed through dedicated tools with defined inputs and behavior.

This makes it possible to reason about exactly what the agent is allowed to do.

Examples include:

- Read and modify project files.
- Search the repository.
- Inspect Git history and changes.
- Manage Python dependencies through `uv`.
- Run Python scripts, modules, and development tools.
- Request explicit user permission before sensitive operations.

The LLM decides which action it wants to perform, but the execution layer determines whether that action is allowed.

```text
User Request
    ↓
Agent Reasoning
    ↓
Tool Selection
    ↓
Security and Permission Checks
    ↓
Tool Execution
    ↓
Result returned to Agent
```

---

### Agent Security

A major part of Wasabi is understanding what happens when an agent is given real execution capabilities.

The security model is based on the principle that **the LLM itself should not be trusted as the security boundary**. Restrictions are enforced by the surrounding execution system.

Current security measures include:

- Project-root filesystem isolation.
- Protection against path traversal.
- Protection against modification outside the repository.
- Project root cannot be deleted.
- Soft deletion instead of permanent file removal.
- Explicit user approval for sensitive operations.
- Initialization-time prompt-injection checks.
- Repository instructions are treated as untrusted data.
- Dedicated tools are preferred over unrestricted command execution.
- Security restrictions remain active during adversarial testing.

Wasabi also explicitly distinguishes between:

```text
Execution failure
→ Diagnose and safely correct.

Permission required
→ Ask the user.

Permission denied
→ Stop the operation.

Security restriction
→ Never attempt circumvention.
```

This distinction became important during adversarial testing.

When instructed to delete its own project, the agent was unable to perform the deletion directly. It then attempted alternative execution paths by generating Bash and Python scripts to achieve the same result.

The project remained intact, but the test exposed an important problem: an agent may interpret a failed or blocked operation as an engineering problem to solve rather than a security boundary.

This led to stricter execution rules:

- Do not recreate blocked operations through another language or tool.
- Do not generate scripts to bypass tool restrictions.
- Do not attempt alternative execution paths after a policy denial.
- User requests cannot override executor security invariants.
- Script execution requires explicit user approval.

---

### Efficient Agent Tooling

The other major focus of Wasabi is making the agent economical to use.

A coding agent that repeatedly reads entire files, reloads the whole repository, or carries unnecessary conversation history wastes:

- Tokens.
- API cost.
- Time.
- Context-window space.
- Model attention.

Wasabi therefore uses specialized tools to retrieve only the information needed for the current task.

The intended workflow is:

```text
Discover
→ Locate
→ Read only relevant context
→ Understand dependencies
→ Apply the smallest correct edit
→ Inspect diff
→ Validate
```

For example:

```text
User asks to modify a function
    ↓
Search for the function
    ↓
Get exact file and line number
    ↓
Read only the relevant lines
    ↓
Apply a precise edit
    ↓
Inspect Git diff
    ↓
Validate the result
```

This avoids treating every source file as a large text blob that must be completely read and rewritten.

---

## Current Features

### Terminal Interface

Wasabi provides a minimal terminal interface that displays:

- User prompts.
- Agent responses with Markdown rendering.
- Thinking state.
- Tool invocations.
- Tool arguments.
- Success and failure states.
- Execution duration.
- Permission prompts for sensitive operations.

The TUI is kept separate from agent logic.

---

## Available Tools

### File Operations

| Tool | Purpose |
| --- | --- |
| `read_file` | Read the contents of a project file. |
| `list_files` | List files and directories within the project. |
| `edit_file` | Replace specified content inside a file. |
| `delete_file` | Move a file to Wasabi's trash directory. |
| `restore_file` | Restore a previously deleted file. |

Deletion is implemented as a reversible operation rather than permanent removal.

---

### Git Operations

| Tool | Purpose |
| --- | --- |
| `git_status` | Inspect the current repository state. |
| `git_diff` | View changes to a file or the repository. |
| `git_diff_summary` | Get a concise summary of modified files and line changes. |
| `git_log` | Inspect recent commits. |
| `git_blame` | Inspect line-level commit and author information. |
| `git_show` | Inspect a specific commit. |

These tools allow the agent to understand repository history and inspect its own changes without unrestricted shell access.

---

### Python and `uv` Operations

| Tool | Purpose |
| --- | --- |
| `uv_version` | Check the installed `uv` version. |
| `uv_sync` | Synchronize the project environment. |
| `uv_tree` | Inspect the dependency tree. |
| `uv_lock` | Generate or update the dependency lockfile. |
| `uv_add` | Add one or more Python dependencies. |
| `uv_remove` | Remove Python dependencies. |
| `uv_run_script` | Run a Python script inside the project environment. |
| `uv_run_module` | Run an importable Python module. |
| `uv_run_command` | Run project development tools such as test runners or linters. |

Code execution and sensitive dependency operations are protected by user approval where required.

Dedicated `uv` tools are preferred over arbitrary shell execution so that each capability has explicit semantics and can be independently controlled.

---

### Search and File Discovery

Wasabi uses `ripgrep` for fast repository-wide search.

| Tool | Purpose |
| --- | --- |
| `search_text` | Search project files and return matching locations with line numbers. |
| `search_text_with_context` | Return matches with surrounding lines for additional context. |
| `find_files` | Find files using filenames or glob patterns. |

This gives the agent a basic repository navigation system:

```text
Don't know the file?
→ find_files

Know a symbol, function, error, or string?
→ search_text

Need surrounding code?
→ search_text_with_context
```

---

## Precise Code Modification

Wasabi is moving away from broad file rewrites toward targeted code operations.

The precise editing layer includes:

- Reading an exact line range.
- Replacing exact, uniquely matching content.
- Replacing only a specific range of lines.
- Inserting content before an exact anchor.
- Inserting content after an exact anchor.
- Atomic file writes.
- File-hash validation to prevent stale edits.

The core invariant is:

> **Modify only the intended region and preserve everything else.**

The intended workflow is:

```text
search_text
    ↓
Find exact file and line
    ↓
read_lines
    ↓
Receive relevant code and file hash
    ↓
Apply surgical edit
    ↓
Verify file has not changed since reading
    ↓
Atomic write
    ↓
Inspect git_diff
```

---

## Repository Understanding

Search and precise editing provide basic code navigation, but larger repositories require structural and semantic understanding.

Wasabi's repository intelligence layer is focused on four components.

### Tree-sitter

Tree-sitter is used to understand the structure of source code.

The planned integration includes:

- Function extraction.
- Class extraction.
- Method extraction.
- Import extraction.
- Symbol boundaries.
- Parent-child relationships.
- Syntax-aware code chunks.
- Changed-symbol detection.

This allows the agent to move from:

```text
Read lines 500–550
```

toward:

```text
Read the Agent._uv_run_script function
```

---

### Global Symbol Index

Tree-sitter output can be used to maintain a searchable index of symbols across the repository.

A symbol entry can contain:

```text
Symbol name
Symbol type
File path
Start position
End position
Parent symbol
```

This allows Wasabi to locate relevant code without repeatedly searching or reading entire files.

---

### Persistent Project Context

Wasabi uses a project-level `WASABI.md` file as persistent repository context.

It is intended to contain durable information such as:

- Project purpose.
- Architecture.
- Important modules.
- Entry points.
- Dependencies.
- Public interfaces.
- Testing commands.
- Security constraints.
- Important engineering decisions.
- Known limitations.

The purpose is not to duplicate source code. It is to preserve the minimum useful understanding of the project across sessions.

When the repository changes, Wasabi should update only the affected sections instead of regenerating the entire context file.

```text
Git diff
    ↓
Identify changed files and symbols
    ↓
Determine semantic impact
    ↓
Update only affected WASABI.md sections
```

---

### Dependency Intelligence

Wasabi aims to understand both external and internal dependencies.

This includes:

- Python dependencies from `pyproject.toml`.
- Dependency relationships from the lockfile.
- Internal imports between modules.
- Reverse dependencies.
- Modules potentially affected by a change.

The goal is practical impact analysis rather than building a complete static-analysis framework.

---

## LSP Integration

Tree-sitter understands code structure, but not complete project semantics.

Language Server Protocol support adds:

- Go to definition.
- Find references.
- Hover and type information.
- Document symbols.
- Workspace symbols.
- Diagnostics.

The intended validation flow is:

```text
Apply precise edit
    ↓
Tree-sitter syntax validation
    ↓
LSP diagnostics
    ↓
Relevant tests
    ↓
Git diff inspection
```

Tree-sitter answers:

> What is the structure of this code?

LSP answers:

> Is this code semantically valid in the context of this project?

---

## Context Compaction

Long-running agent sessions accumulate conversation history, tool calls, tool results, errors, and intermediate reasoning.

Keeping all of this indefinitely wastes context-window space and API tokens.

Wasabi's context-compaction layer is intended to monitor token usage and periodically compress older context while preserving:

- System instructions.
- Current task.
- Important project context.
- Recent tool activity.
- Unresolved errors.
- Decisions relevant to ongoing work.

The goal is simple: **retain operational continuity without carrying unnecessary history forever.**

---

## Security Measures

The current security model includes:

### Project-Root Isolation

All filesystem operations are constrained to the active repository.

The execution layer protects against:

- Absolute-path escapes.
- `..` traversal.
- Access outside the project.
- Deletion of the project root.

### Soft Deletion

Files are moved to a recoverable trash directory instead of being permanently deleted.

### User Permission

Sensitive operations require explicit `y/N` approval before execution.

This includes code execution and other operations classified as destructive or security-sensitive.

### Prompt-Injection Checks

During initialization, repository instruction files can be inspected for potentially malicious instructions before they influence agent behavior.

### Controlled Execution

Dedicated tools are used instead of unrestricted shell access wherever possible.

Subprocess operations use explicit argument lists rather than shell-string interpolation where applicable.

### Bypass Prevention

A denied or restricted operation must not be recreated through:

- Another tool.
- Another language.
- Generated Bash or Python scripts.
- Subprocesses.
- Module execution.
- Alternative command paths.

Security enforcement exists outside the LLM because instructions alone are not considered a sufficient security boundary.

---

## Adversarial Testing

Wasabi is tested against scenarios such as:

- Direct project deletion attempts.
- Generating Bash scripts to perform denied actions.
- Generating Python scripts as an alternative execution path.
- Attempting execution through `uv`.
- Path traversal.
- Symlink-based project-root escapes.
- Prompt injection through repository files.
- Requests to disable security mechanisms.
- Attempts to reinterpret policy denials as ordinary tool failures.

The desired invariant is:

> **The model may propose an unsafe action, but the execution layer should prevent unauthorized effects.**

---

## Current Scope

The remaining engineering scope for Wasabi is intentionally bounded:

- Precise reads and surgical edits.
- Atomic writes and stale-file protection.
- Tree-sitter integration.
- Global symbol index.
- Persistent `WASABI.md` project context.
- Incremental project-context updates.
- Dependency intelligence.
- LSP client and persistent language-server loop.
- Edit-validation pipeline.
- Context compaction.
- Python package and CLI distribution.
- Integration testing.
- Adversarial security testing.

The following are intentionally out of scope:

- Multi-agent orchestration.
- Vector databases.
- Embedding-based semantic memory.
- MCP integration.
- Autonomous background workers.
- Model training or fine-tuning.
- Self-learning or persistent lesson memory.

---

## Project Direction

Wasabi is not intended to be the largest possible coding-agent framework.

It is a focused engineering project for understanding:

- How an LLM should receive controlled access to real execution capabilities.
- Where security enforcement should exist outside the model.
- How agents behave when their actions are denied or restricted.
- How repository navigation can be made more precise and economical.
- How unnecessary file reads and context usage can be reduced.
- How structural and semantic tools can improve code understanding.
- How agent context can remain useful without growing indefinitely.

The aim is to implement these mechanisms directly, test their behavior, understand their failure modes, and document the engineering trade-offs involved.