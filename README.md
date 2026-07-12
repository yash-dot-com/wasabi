# Wasabi

<p align="center">
  <img src="static/Wasabi-Header.png" width="1100" alt="Wasabi Logo">
</p>

## About

Wasabi is a Python-first terminal coding agent I built to understand the engineering behind **agentic systems, secure agent execution, code intelligence, and efficient context management**.

The project is primarily a hands-on exploration of how coding agents work internally: how an LLM reasons through multi-step tool workflows, interacts with a real repository, executes actions under controlled permissions, understands source code structurally, and remains observable and testable.

## Engineering Focus

## Performance and Efficiency

Wasabi implements advanced file mutation tools that significantly enhance the editing and writing capabilities of the agent. Here's how these features contribute to improved token usage efficiency:

- **Surgical Edits**: By allowing precise modifications without reading entire files, Wasabi reduces unnecessary token usage and focuses on quality content updates.

- **Atomic Operations**: Ensures that changes are applied in a single operation, preventing partial updates that could require additional tokens to correct.

- **File Integrity Checks**: By validating files before mutations, Wasabi avoids staleness and ensures that edits are relevant, which maintains the quality of output without wasting tokens on invalid transformations.

- **Dynamic Context Management**: This feature allows the agent to adapt content actively based on current requirements, leading to more meaningful text generation with fewer tokens.

- **Enhanced Interaction**: With the capability to manage both text and structure, agents can execute complex edits that optimize content for clarity and relevance, improving the overall quality-to-token ratio.

By maintaining a high-quality output while minimizing token usage, Wasabi enhances productivity and reduces API costs associated with language model interactions.

- **Completion Testing** — testing the ability to replace and insert commands.

Wasabi explores:

- **Agentic workflows** — designing tools that an LLM can combine and reason over to complete multi-step software engineering tasks.
- **Controlled agent execution** — giving an agent useful filesystem, Git, dependency, search, and execution capabilities without unrestricted access to the host system.
- **Agent security** — project-root isolation, user permissions for sensitive operations, prompt-injection checks, execution restrictions, and protection against indirect attempts to bypass denied actions.
- **Code intelligence** — using Tree-sitter, AST-based code analysis, symbol indexing, dependency graphs, and LSP integration to help the agent understand code beyond raw text.
- **Efficient context management** — precise reads, surgical edits, persistent project context, and context compaction to reduce unnecessary token usage and API cost.
- **Monitoring and evaluation** — understanding how to observe agent actions, trace tool usage, evaluate task outcomes, measure failures, and test agent behavior under normal and adversarial conditions.
- **Agent security research** — studying vulnerabilities that real-world agentic products face, including prompt injection, tool misuse, excessive agency, indirect execution bypasses, malicious repository content, unsafe code execution, and confused-deputy-style behavior.

## Implementation Status

#### Wasabi now has ability to surgically read, write and edit files. 
- lesser tokens used and more efficient and accurate editing.

### Completed

- [x] Core agent loop with OpenAI tool calling
- [x] Tool execution layer
- [x] System information tools
- [x] Filesystem tools
- [x] Project-root protection
- [x] Soft deletion and file restoration
- [x] Git tools
- [x] Prompt-injection check during initialization
- [x] User permission mechanism for destructive and sensitive operations
- [x] System prompt security hardening
- [x] `uv` tooling
  - [x] Version
  - [x] Sync
  - [x] Dependency tree
  - [x] Add packages
  - [x] Remove packages
  - [x] Run scripts
  - [x] Run modules
  - [x] Run commands
- [x] Ripgrep-based text search
- [x] Search with surrounding context
- [x] File discovery
- [x] Minimal clean TUI

### Remaining 

#### Precise Reads and Surgical Edits
- [ ] Read exact line ranges with line numbers
- [ ] Replace exact code blocks
- [ ] Replace specific line ranges
- [ ] Insert before an exact anchor
- [ ] Insert after an exact anchor
- [ ] Atomic writes
- [ ] File-hash validation for stale edits

#### Tree-sitter and Code Intelligence
- [ ] Tree-sitter integration
- [ ] Extract functions, classes, methods and imports
- [ ] Build a global symbol index
- [ ] Read code by symbol
- [ ] Precise symbol-level edits

#### Project Context
- [ ] Generate persistent `WASABI.md` project context
- [ ] Keep architecture, important modules, dependencies and project decisions in context
- [ ] Update only affected sections when the project changes

#### Dependency Intelligence
- [ ] Build internal module dependency relationships
- [ ] Identify reverse dependencies and affected modules

#### LSP Integration
- [ ] Implement LSP client
- [ ] Maintain persistent language-server process
- [ ] Definitions
- [ ] References
- [ ] Diagnostics
- [ ] Validation loop after edits

#### Context Compaction
- [ ] Track token usage from OpenAI API responses
- [ ] Compact old context when a threshold is reached
- [ ] Preserve active task, important project context, unresolved errors and recent actions

#### Distribution and Finalization
- [ ] Create distributable Python package
- [ ] Add CLI entry point
- [ ] Final integration testing
- [ ] Final adversarial security testing
- [ ] README cleanup