# Wasabi

<p align="center">
  <img src="static/Wasabi-Header.png" width="1100" alt="Wasabi Logo">
</p>

## Overview

Wasabi is a Python-first terminal coding agent built to explore the engineering problems involved in giving an LLM controlled access to a software repository.

The project focuses on four areas:

- **Tool use** — filesystem, Git, dependency management, search, and code execution.
- **Repository understanding** — project structure, symbols, dependencies, and persistent project context.
- **Precise code modification** — targeted reads and surgical edits that preserve unrelated file content.
- **Agent security** — project-root isolation, prompt-injection checks, explicit user approval for sensitive operations, and protection against indirect policy bypasses.

Wasabi is intentionally being developed as a focused coding-agent implementation rather than a general-purpose autonomous system. The goal is to understand and implement the core mechanisms behind repository-aware coding agents while keeping the system small enough to reason about, test, and secure.

---

## Current Capabilities

### Terminal Interface

Wasabi provides a minimal terminal interface for interacting with the agent.

The interface displays:

- User prompts
- Agent responses with Markdown rendering
- Thinking state
- Tool invocations
- Tool arguments
- Execution status
- Execution duration
- Permission requests for sensitive operations

The TUI is kept separate from agent logic so that presentation does not affect reasoning, tool execution, or security enforcement.

---

## Tool System

Wasabi exposes explicit tools to the model rather than unrestricted access to the host environment.

The agent can combine multiple tools when a task requires several steps. For example:

```text
Find relevant file
→ Search for symbol
→ Read surrounding code
→ Apply precise edit
→ Inspect Git diff
→ Validate result
```

Tool access is constrained by project-root validation, execution policies, and user approval where required.

### File Tools

- `read_file`: Reads the contents of a file inside the project root.
- `list_files`: Lists files and directories within a specified project path.
- `edit_file`: Replaces specified text inside an existing file. This is being supplemented by more precise editing operations to avoid unnecessary full-file modifications.
- `delete_file`: Performs a soft deletion by moving a file into Wasabi's trash directory instead of permanently removing it.
- `restore_file`: Restores a previously deleted file from the trash directory to its original location.

### Git Tools

- `git_status`: Returns the current repository state, including modified, staged, and untracked files.
- `git_diff`: Shows changes for a specific file or the repository.
- `git_diff_summary`: Returns a concise summary of changed files, insertions, and deletions.
- `git_log`: Returns recent commits with a configurable result limit.
- `git_blame`: Shows commit and author information associated with individual lines of a file.
- `git_show`: Inspects a specific commit by its hash.

These tools allow the agent to inspect repository history and current changes without requiring unrestricted shell access.

### Python and uv Tools

Wasabi uses dedicated uv tools for Python project and dependency operations.

- `uv_version`: Returns the installed uv version.
- `uv_sync`: Synchronizes the project's environment with its dependency metadata and lockfile.
- `uv_tree`: Displays the project's dependency tree.
- `uv_lock`: Generates or updates the project's lockfile.
- `uv_add`: Adds one or more Python dependencies.
- `uv_remove`: Removes one or more Python dependencies.
- `uv_run_script`: Runs a specific Python script inside the project's managed environment.
- `uv_run_module`: Runs an importable Python module through Python's module system.
- `uv_run_command`: Runs a command-line executable available inside the project's managed environment, such as a test runner, linter, formatter, or type checker.

Code execution and dependency-changing operations are subject to explicit user approval where appropriate.

### Search and Discovery Tools

Wasabi uses ripgrep for fast repository-wide text search and file discovery.

- `search_text`: Searches project files for a string or pattern and returns matching locations with file paths and line numbers.
- `search_text_with_context`: Searches for text and includes a configurable number of surrounding lines.
- `find_files`: Finds project files using filenames or glob patterns while respecting repository ignore rules.

This allows the agent to inspect nearby code without reading an entire file.

Examples:

- `*.py`
- `test_*.py`
- `pyproject.toml`
- `src/*.py`

These tools form the first stage of Wasabi's code-navigation workflow:

1. Unknown location
2. `find_files` or `search_text`
3. Identify the exact file and line
4. Read only the relevant code
5. Perform a targeted modification

### Precise Code Modification

A major focus of Wasabi is reducing unnecessary full-file reads and rewrites.

The intended editing workflow is:

1. Discover
2. Locate
3. Read the relevant region
4. Understand the surrounding code
5. Apply the smallest correct edit
6. Inspect the diff
7. Validate

The precise editing layer includes or is planned to include:

- `read_lines`: Reads only a specified line range from a file and returns line numbers.
- `replace_exact`: Replaces an exact, uniquely matching block of text.

The operation is rejected when:

- The target does not exist.
- The target occurs multiple times and is ambiguous.

- `replace_lines`: Replaces only a specified line range while preserving all content before and after it.
- `insert_before`: Inserts new content before an exact anchor.
- `insert_after`: Inserts new content after an exact anchor.

### File Hash Validation

A file hash can be captured when code is read and checked before a later edit. If the file changed between reading and editing, the operation is rejected as stale.

### Atomic Writes

File modifications are written to a temporary file before atomically replacing the original. This reduces the risk of leaving a partially written file after an interrupted operation.

The core invariant is:

> An edit should modify only the intended region. Unrelated content should remain unchanged.

### Security Model

Wasabi treats the LLM as a decision-making component, not as the security boundary. Restrictions are enforced in code around filesystem access, command execution, and tool dispatch.

### Project-Root Isolation

Filesystem operations are restricted to the active project root.

The validation layer is designed to prevent:

- Absolute-path escapes
- `..` path traversal
- Access outside the repository
- Accidental modification of unrelated host files

The project root itself is protected from deletion.

### Soft Deletion

File deletion moves files to a dedicated trash directory rather than permanently deleting them.

This provides:

- Recovery from accidental deletion
- Safer autonomous file operations
- A reversible default for destructive actions

The agent also has a dedicated restoration tool.

### User Approval for Sensitive Operations

Sensitive operations require explicit user confirmation through a y/N permission prompt.

Examples include:

- Script execution
- Python module execution
- Arbitrary project command execution
- Dependency addition or removal
- Destructive Git operations
- Other explicitly classified destructive actions

The permission mechanism is enforced at the execution layer rather than relying only on instructions to the model.

### Prompt-Injection Check During Initialization

During project initialization, Wasabi checks repository instruction files for potentially malicious or manipulative content before allowing them to influence agent context.

Relevant files can include:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`

The purpose is to treat repository-provided instructions as untrusted input rather than automatically granting them authority over the agent.

### Policy-Boundary Enforcement

Wasabi distinguishes between:

- Execution failure → Diagnose and safely correct
- Permission required → Ask the user
- Permission denied → Stop the operation
- Security restriction → Do not attempt circumvention

The agent is explicitly instructed not to recreate blocked operations through:

- Another tool
- Another programming language
- Generated scripts
- Python subprocesses
- Shell interpreters
- Module execution
- Indirect command execution

This behavior was motivated by adversarial testing in which the agent was instructed to delete its own project. When direct deletion was unavailable, the model attempted alternative execution paths by creating Bash and Python scripts. The project was not deleted, but the test exposed the need to treat policy denial and ordinary tool failure as fundamentally different outcomes.

This led to stricter system instructions and explicit user approval for code execution.

### Restricted Command Execution

Wasabi does not expose an unrestricted shell directly to the model.

Dedicated tools are preferred for:

- Git operations
- Python dependency management
- File operations
- Search
- Code execution

Subprocess execution uses argument lists rather than shell-string interpolation where possible, reducing exposure to shell injection and command chaining.

### Repository Understanding

Wasabi's repository-understanding layer is designed around progressive retrieval rather than loading an entire codebase into the model context.

The intended flow is:

1. User task
2. Read persistent project context
3. Locate relevant files and symbols
4. Retrieve definitions and references
5. Inspect direct dependencies and related tests
6. Build a bounded task context
7. Modify and validate

### Tree-sitter Integration

Tree-sitter provides structural understanding of source code through concrete syntax trees.

The planned integration covers:

- Language detection
- Source parsing
- Function extraction
- Class extraction
- Method extraction
- Import extraction
- Export extraction
- Symbol boundaries
- Parent-child symbol relationships
- Syntax-aware code chunks
- Symbol lookup
- Changed-symbol detection

This enables operations such as:

- `read_symbol("Agent._uv_run_script")`
- `replace_symbol("Agent._uv_run_script", new_implementation)`

instead of relying exclusively on raw line numbers or text matching.

Tree-sitter answers:

- What is the structure of this code, and where exactly is a symbol located?

### Global Symbol Index

Tree-sitter output will be used to build a repository-wide symbol index containing information such as:

- Symbol name
- Symbol type
- File path
- Start position
- End position
- Parent symbol
- Imports
- Exports

This gives the agent a searchable structural map of the repository without repeatedly reading complete files.

The index is intended to be updated incrementally when files change.

### Persistent Project Context

Wasabi uses a project-level context file, WASABI.md, as a concise persistent representation of the repository.

It can contain:

- Project purpose
- Technology and dependencies
- Architecture
- Directory structure
- Entry points
- Important modules
- Public interfaces
- Data models
- Configuration
- Commands
- Testing
- Security constraints
- Architectural decisions
- Current implementation state
- Known issues

The purpose of WASABI.md is not to duplicate source code. It stores durable information needed to understand the project across sessions.

### Incremental Context Updates

When the repository changes, Wasabi should avoid regenerating the complete project context.

The intended workflow is:

1. Git diff
2. Identify changed files
3. Determine changed symbols
4. Classify semantic impact
5. Map changes to affected WASABI.md sections
6. Update only those sections
7. Preserve everything else

For example:

- Dependency changed → Update Dependencies
- New module added → Update Architecture and Important Modules
- Public interface changed → Update Public Interfaces
- Security policy changed → Update Security Constraints
- Internal implementation detail changed → No project-context update required

### Dependency Intelligence

Wasabi's dependency understanding is intended to cover both external packages and internal module relationships.

This includes:

- Parsing `pyproject.toml`
- Reading lockfile information
- Distinguishing direct and development dependencies
- Extracting internal imports
- Building an internal dependency graph
- Finding reverse dependencies
- Determining which modules may be affected by a change

The goal is practical impact analysis rather than a complete static-analysis framework.

### LSP Integration

Tree-sitter provides structural information, but it does not provide full semantic understanding.

Wasabi therefore uses the Language Server Protocol as a complementary validation layer.

The LSP client is intended to support:

- Go to definition
- Find references
- Hover and type information
- Document symbols
- Workspace symbols
- Diagnostics

The language server remains alive during the Wasabi session rather than restarting after every operation.

The validation flow is:

1. Apply a precise edit
2. Parse with Tree-sitter
3. Synchronize the change with LSP
4. Receive diagnostics
5. Repair if necessary
6. Run relevant tests
7. Inspect the Git diff

Tree-sitter answers:

- What is the structure of the code?

LSP answers:

- Is the code semantically valid within this project?

### Context Compaction

Long agent sessions accumulate:

- User messages
- Assistant reasoning and responses
- Tool calls
- Tool outputs
- Errors
- Intermediate implementation details

Wasabi's context-compaction layer is intended to monitor token usage and reduce old context before the model's context window becomes unnecessarily large.

Compaction should preserve:

- System instructions
- Current user task
- Important project context
- Recent tool activity
- Unresolved errors
- Decisions that affect ongoing work

Older conversational details can be summarized into a smaller representation.

The goal is to preserve operational continuity while reducing unnecessary token usage.

### Validation Strategy

Wasabi's intended code-change validation pipeline is:

1. Precise edit
2. Inspect Git diff
3. Tree-sitter syntax validation
4. LSP diagnostics
5. Type checker
6. Linter
7. Relevant tests

Not every task requires every validation step. The agent should choose validation proportional to the change.

### Adversarial Security Testing

The security layer is tested against scenarios such as:

- Direct project deletion
- Bash script generated to delete the project
- Python script generated to delete the project
- Moving a destructive script into another directory before execution
- Attempting execution through uv run
- Path traversal
- Symlink-based project-root escape
- Prompt injection from repository files
- Requests to disable security checks
- Attempts to recreate denied operations through alternative tools

The desired invariant is:

> The model may propose an unsafe action, but the execution and policy layers must prevent unauthorized effects.

### Architecture Direction

The overall architecture is intentionally layered:

```text
User
  ↓
Terminal Interface
  ↓
Agent
  ↓
Tool Selection
  ↓
Security / Permission Checks
  ↓
Tool Execution
  ↓
Filesystem / Git / uv / Search / Tree-sitter / LSP
  ↓
Validation and Git Diff
```

The LLM decides what action it wants to perform. The surrounding system decides whether that action is permitted and how it is executed.

### Current Development Scope

The current completion scope for Wasabi is:

- Precise reads and surgical edits
- Atomic writes and stale-file protection
- Tree-sitter integration
- Global symbol index
- Persistent WASABI.md project context
- Incremental context updates
- Dependency intelligence
- LSP client and persistent language-server loop
- Edit-validation pipeline
- Context compaction
- Minimal terminal interface
- Python package and CLI distribution
- Integration and adversarial testing

The terminal interface, Git tools, uv tools, search tools, user-permission mechanism, project-root protection, soft deletion, and initialization-time prompt-injection checking are already implemented.

### Out of Scope

To keep the project bounded, the following are not part of the current implementation scope:

- Multi-agent orchestration
- Vector databases
- Embedding-based semantic memory
- Browser automation
- MCP integration
- Autonomous background workers
- Model training or fine-tuning
- A complete static-analysis engine
- Self-learning or persistent lesson memory

These may be explored separately, but they are not required for Wasabi's completion.

### Summary

Wasabi is a small coding-agent implementation focused on repository navigation, controlled tool execution, precise code modification, project context, and security boundaries.

The project is primarily an engineering exercise in answering a few practical questions:

- How should an LLM navigate a repository without repeatedly reading everything?
- How can it make targeted modifications without rewriting unrelated code?
- How should tool execution be constrained and approved?
- How can repository structure and semantics be exposed through Tree-sitter and LSP?
- How should project context remain useful as the codebase changes?
- What happens when an agent actively attempts to work around its own restrictions?

The objective is not to build the largest possible agent framework. It is to implement these mechanisms clearly, test their behavior, document their limitations, and understand the engineering trade-offs involved.