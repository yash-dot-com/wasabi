# Wasabi

<p align="center">
  <img src="static/Wasabi-Header.png" width="1100" alt="Wasabi Logo">
</p>

## About

Wasabi is a Python-first terminal coding agent I built to understand the engineering behind **agentic systems, secure agent execution, code intelligence, and efficient context management**.

The project is primarily a hands-on exploration of how coding agents work internally: how an LLM reasons through multi-step tool workflows, interacts with a real repository, executes actions under controlled permissions, understands source code structurally, and remains observable and testable.

## Engineering Focus

Wasabi explores:

- **Agentic workflows** — designing tools that an LLM can combine and reason over to complete multi-step software engineering tasks.
- **Controlled agent execution** — giving an agent useful filesystem, Git, dependency, search, and execution capabilities without unrestricted access to the host system.
- **Agent security** — project-root isolation, user permissions for sensitive operations, prompt-injection checks, execution restrictions, and protection against indirect attempts to bypass denied actions.
- **Code intelligence** — using Tree-sitter, AST-based code analysis, symbol indexing, dependency graphs, and LSP integration to help the agent understand code beyond raw text.
- **Efficient context management** — precise reads, surgical edits, persistent project context, and context compaction to reduce unnecessary token usage and API cost.
- **Monitoring and evaluation** — understanding how to observe agent actions, trace tool usage, evaluate task outcomes, measure failures, and test agent behavior under normal and adversarial conditions.
- **Agent security research** — studying vulnerabilities that real-world agentic products face, including prompt injection, tool misuse, excessive agency, indirect execution bypasses, malicious repository content, unsafe code execution, and confused-deputy-style behavior.

## Implementation Status

### Completed

- [x] OpenAI-powered agent loop with tool calling
- [x] Multi-step agentic tool workflows
- [x] Centralized tool execution layer
- [x] Minimal terminal interface with Markdown rendering and tool-call visibility

#### Filesystem
- [x] Read files
- [x] List files and directories
- [x] Edit files
- [x] Soft-delete files to a recoverable trash directory
- [x] Restore deleted files
- [x] Project-root validation

#### Git
- [x] Git status
- [x] Git diff
- [x] Git diff summary
- [x] Git log
- [x] Git blame
- [x] Git show

#### Python and `uv`
- [x] Check `uv` version
- [x] Synchronize project dependencies
- [x] Inspect dependency tree
- [x] Add and remove Python packages
- [x] Run Python scripts
- [x] Run Python modules
- [x] Run project development commands

#### Repository Search
- [x] Repository-wide text search with `ripgrep`
- [x] Exact file and line-number discovery
- [x] Search with surrounding context
- [x] File discovery using glob patterns
- [x] `.gitignore`-aware search

#### Agent Security
- [x] Project-root filesystem isolation
- [x] Path traversal protection
- [x] Protection against deleting the project root
- [x] Explicit `y/N` permission for sensitive operations
- [x] User approval before script and code execution
- [x] Prompt-injection checks during initialization
- [x] Repository content treated as untrusted data
- [x] Rules against recreating denied operations through alternative tools, scripts, languages, or execution paths
- [x] Initial adversarial testing against project deletion and tool-restriction bypasses

## In Progress / TODO

#### Precise Reads and Surgical Edits
- [ ] Read exact line ranges with line numbers
- [ ] Replace exact and uniquely matching code
- [ ] Replace specific line ranges
- [ ] Insert code before an exact anchor
- [ ] Insert code after an exact anchor
- [ ] Preserve unrelated file content
- [ ] Atomic file writes
- [ ] File-hash validation to prevent stale edits

#### Tree-sitter and AST-Based Code Intelligence
- [ ] Parse source files into syntax trees
- [ ] Extract functions, classes, methods, imports, and symbols
- [ ] Identify exact symbol boundaries
- [ ] Build a repository-wide symbol index
- [ ] Read code by symbol
- [ ] Modify code by symbol
- [ ] Track structural relationships between symbols and modules

#### Dependency Intelligence
- [ ] Extract internal imports and module relationships
- [ ] Build a dependency graph
- [ ] Find reverse dependencies
- [ ] Determine modules affected by a code change

#### Persistent Project Context
- [ ] Generate project-level `WASABI.md`
- [ ] Store architecture, modules, entry points, dependencies, interfaces, testing commands, and security constraints
- [ ] Detect repository changes
- [ ] Update only affected `WASABI.md` sections

#### LSP Integration
- [ ] Implement LSP client
- [ ] Maintain a persistent language-server process
- [ ] Go to definition
- [ ] Find references
- [ ] Hover and type information
- [ ] Document and workspace symbols
- [ ] Diagnostics and error detection

#### Context Compaction
- [ ] Track token usage from OpenAI API responses
- [ ] Define context-compaction thresholds
- [ ] Compact old conversation and tool history
- [ ] Preserve current task, project context, recent actions, unresolved errors, and security instructions

#### Monitoring and Evaluation
- [ ] Trace agent actions and tool calls
- [ ] Record execution outcomes and failures
- [ ] Build evaluation cases for normal coding tasks
- [ ] Build adversarial security evaluations
- [ ] Evaluate tool misuse and permission-boundary behavior
- [ ] Research security vulnerabilities affecting production agentic systems

#### Distribution
- [ ] Clean Python package structure
- [ ] Add CLI entry point
- [ ] Build distributable Python package
- [ ] Test installation in a clean environment

## Core Principle

Wasabi is built around one central question:

- **How can an AI agent be given enough capability to perform useful engineering work while keeping its execution controlled, observable, secure, and economical?**

- The goal of the project is not to build the largest coding-agent framework. It is to directly implement and understand the systems behind practical agentic software