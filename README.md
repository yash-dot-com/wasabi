<p align="left">
  <img src="https://github.com/user-attachments/assets/3e51cc40-e78b-4d5a-a18c-a142125ed95c" width="300" alt="Wasabi Logo">
</p>

## Wasabi

A secure, Python-first coding agent focused on understanding, modifying and reasoning about software projects with minimal tool surface and maximum code awareness.

## Design Philosophy

* Security by default
* Less tools, better reasoning
* Semantic code understanding over text search
* Git-aware and incremental context updates
* Minimize token usage through caching and intelligent context management

## 9th july - learning

- LSP
How the Loop Works
1. Al generates code (with intentional bugs in the demo)
2. LSP analyzes the code using TypeScript's language server
3. Diagnostics returned (errors, warning with line numbers)
4. Formatted for AI - errors converted to human-readable format
5. AI fixes errors and submits new code
6. Repeat until no errors remain (max 5 iterations)

## Day 1 - 11th july 2026
- uv tools - add, remove, lock file remains - there is vulnerability with exposing the lock files because that exposes dependency hacking 
- add user permission flow 
```
Agent requests sensitive tool
        ↓
Tool checks: requires_permission?
        ↓
      Yes
        ↓
Prompt user [y/N]
    ↙         ↘
   y           n
   ↓           ↓
Execute       Deny
```
- [DONE] : adding uv lock, uv run script, module and command - scoping the uv run command to avoid misuse by agent. lock for resolving dependencies, run scripts to run python files, run module to run importable files, run command to run ruff linter, pytest, mypy basically command line tools 
- [DONE] : Text search - using ripgrep as fast search utility
- about ripgrep : rg "search_string" -n : returns files in which the search string is present along with line number on which it is present
```js
-n          Show line numbers
-H          Always show file paths
-i          Case-insensitive search
-F          Treat query as literal text, not regex
-C 3        Show 3 lines of context around matches
-g "*.py"   Search only Python files
--hidden    Include hidden files
```
- --json mode : outputs a json string for result we are implementing json results
- JSON lines describing each match, including: file path, matched text, line number, byte offset
- [CURRENTLY] : File discovery using ripgrep 
```js
Agent wants to find:
- all Python files
- a specific filename
- test files
- config files

Example usage: 
find_files("*.py")
find_files("test_*.py")
find_files("pyproject.toml")
```
- Precise reads
- Exact replacement
- Insert operations
- Atomic writes
- File hashes
- Script permissions
- System-prompt hardening
- implement a way to make sure all the dependencies are available for the agent, need to create single installation script to install dependencies as well as the agent code.

## Day 1 - 11th july 2026
- Tree-sitter integration
- Repository discovery
- Global symbol index
- Import extraction
- Dependency graph
- Initial WASABI.md
- Incremental context update- - s

## Day 2 - 12th july 2026
- Complete surgical-edit system
- Symbol reads
- Symbol replacement
- Git-aware indexing
- Context retrieval
- LSP client
- Persistent LSP server loop

## Day 2 - 12th july 2026
- LSP diagnostic loop
- Edit validation
- Automatic rollback
- Unit tests
- Integration tests
- Adversarial tests
- README
- Architecture documentation
- Demo
- add better TUI (cosmetic changes)

## states used in agent
- tree sitter index : quick code traversal & understanding
- wasabi.md : overall project understanding
- lsp : semantically correct code checker

## extras 
- self learning system : global, project specific
- lessons.json : stores project-specific learnings.
- dockerized / firecracker isolated execution of code 

# Architecture

## Core Capabilities

### Security

* Startup prompt injection / agent poisoning scan
* Project root filesystem sandbox

### Filesystem

* Read / Write / Replace / Delete
* Directory traversal
* File search

### Git

* Status
* Diff
* Log
* Show
* Blame
* Restore

### Python (uv)
- need to create a user approval mechanism to approve running any scripts / files using python.
- shell scripts can be written in python and bypass the command check. 
- need to create a strict command parser and only allow whitelisted cmds 
- need to find a way to avoid clever shell scripting & execution of python scripts with shell functions.
* Run scripts
* Pytest
* Ruff
* Mypy
* Compile checks

### Search

* Fast repository search (ripgrep)
* File search (ripgrep)

### Diagnostics

* Environment
* Project information
* Tool versions

### Semantic Understanding

* Tree-sitter
* LSP
* Symbol indexing
* Reference tracking
* Call hierarchy
* Structural editing

---

# Development Roadmap

## Phase 1 — Functional Coding Agent

* Security
* Filesystem
* Git
* Python
* Search
* Diagnostics

**Goal:** Ship a secure and usable coding agent.

---

## Phase 2 — Repository Understanding

Build a one-time repository snapshot containing:

* Directory tree
* README
* AGENTS.md
* pyproject.toml
* Dependencies
* Entry points
* Project metadata

---

## Phase 3 — Semantic Code Intelligence

Integrate:

* Tree-sitter
* LSP
* Symbol graph
* Dependency graph
* Call graph

Move from file-based reasoning to architecture-aware reasoning.

---

## Phase 4 — Context Engine

Maintain a continuously updated workspace model.

Features:

* Cached repository state
* Semantic summaries
* Symbol index
* Git state
* Dependency graph
* Incremental cache invalidation using Git changes

Purpose:

Avoid repeatedly loading the repository while maintaining an accurate understanding of the project.

---

## Phase 5 — Multi-Agent Workspace

The primary coding agent focuses exclusively on reasoning and implementation.

Background agents continuously maintain project knowledge by:

* Updating documentation
* Refreshing repository summaries
* Rebuilding symbol indexes
* Updating dependency graphs
* Refreshing semantic context after code changes
* Maintaining cached workspace state

This keeps the primary agent's context focused on solving the current task rather than performing maintenance work.

---

## Phase 6 — Intelligent Editing

Perform semantic edits instead of text replacement.

Examples:

* Rename symbols safely
* Move functions
* Update references
* Structural refactoring
* Multi-file edits

---

# Target Agent Workflow

```
Task
    ↓
Understand Repository
    ↓
Search & Navigate
    ↓
Plan
    ↓
Implement
    ↓
Run Quality Checks
    ↓
Run Tests
    ↓
Review Git Diff
    ↓
Self Review
    ↓
Return Result
```

Background agents continuously update repository knowledge while the primary agent works.

---

# Current Progress

## Completed

* [x] Startup security scan
* [x] Prompt injection detection
* [x] Project root sandbox
* [x] Filesystem CRUD tools

## Next

* [ ] Git tools
* [ ] Python (uv) tools
* [ ] Search
* [ ] Diagnostics
* [ ] Tree-sitter
* [ ] LSP
* [ ] Context engine
* [ ] Multi-agent workspace

# OLD DOCUMENTATION BELOW

## learning - 6th july 2026
- not allowing the agent to directly work with command line tools or execute any commands.
- understand how the command tools operate first
- cmd tools put their output as two possible things 
      - stdout - for standard outputs
      - stderr - for any errors that may have occurred.
- for enabling the agent to work with command line tools, I have designed the following mechanism 
- scoped and controlled execution of commands & proper JSON based output for agents to understand the execution result. 
- instead of
```
LLM
  │
  ▼
run_command("git status")
``` 
- we will be doing the following 
```
LLM
  │
  ▼
git_status()
  │
  ▼
run_command(["git", "status", "--short", "--branch"])
```

## subprocesses for executing cmds safely 
- A subprocess is simply another program that your Python program starts.
- git, python, ruff, pytest are another programs that agent can start (spawn) as background / parallel tasks
- the subprocess returns outputs of the executed program 
- the main program - agent continues even after the subprocess ends.

```
Agent
    ↓
Tool
    ↓
subprocess
    ↓
Operating System
    ↓
Git / Ruff / Pytest
```

## security concerns & mechanism for subprocess safety
- subprocess talks directly to the operating system, it's your largest attack surface.
- Wasabi follows a capability-based security model. The LLM never executes arbitrary shell commands or interacts directly with the operating system. Every action must go through a predefined tool with a fixed scope.

## Security

- Startup prompt injection / agent poisoning detection.
- Project root sandbox (no filesystem access outside the repository).
- No generic shell tool exposed to the agent.
- Capability-based execution (Git, Python, Search, etc. only).
- `subprocess.run(..., shell=False)` to prevent shell injection.
- Hardcoded executables and arguments (agent never chooses binaries).
- Fixed working directory (`cwd=PROJECT_ROOT`).
- Execution timeouts for all subprocesses.
- Structured stdout/stderr capture.
- Large output truncation before returning results to the LLM to prevent excessive memory usage and token consumption.
- Consistent error handling with structured tool responses.

## git tooling

- git diff : to check changes changes across file. 
- git status : check the current status of repository
- git log(limit=20) 
- git show(commit)
- git blame
- git restore 
- git add(list[str])
- git commit : requires user permission

## python tooling 

## uv tooling

## environment diagnostic tooling 

## search tooling 
- search_text 
- search_files 

## roadmap 
- WOKRING ON : git helper tools, see research & techniques in dedicated section below 
- secure shell execution environment - implementing whitelisting vs blacklisting strategy
- surgical edits
- tool - shell tool for executing scripts & reading their output from terminal 
- undo file - so that previous code can be recovered
- create single source of truth for code
- web search fn - to fetch new documentation 
- security measure - blacklisting harmful scripts execution
- security measure - ask user for permission while running scripts 
- multi-agents task distribution and follow-up pipeline 
- background tasks 
- IMP : fix decision fatigue for agent by narrowing down and pin-pointing system prompt for better tool usage 
- IMP : build evaluation system for evaluating agent harness 
- DONE : system security check 
- DONE : system diagnostics run - check for prompt injections, system poisoning : check src/system_check.py
- DONE: security measures - prevent edits in files other than current working directory 
- DONE : delete and restore file from trash folder

## comparisonal development, getting design inspiration from following repos. 
- omp : oh-my-pi meta harness built over pi (omp)[https://github.com/can1357/oh-my-pi]
- pi : (pi)[https://github.com/earendil-works/pi]
- lightcode : (lightcode)[https://github.com/Kartik-2239/lightcode]

## tools 
- list of all tools avaiable 
- filesystem - read, write, replace-in-file, delete, list dirs, search files
- git - status, diff, log, blame, show, restore
- uv / python - uv run, pytest, ruff, ruff_format, mypy, compile, compile_project, python_version, pip_list 
- search - ripgrep 
- logs - head, tail
- security - startup security scan, project root protection
- misc - project tree, read multiple files at once, glob search, symbol search, read json, toml, lock files, diagnotics - return python version, os, uv verson, cwd, git branch 
- environment integration - TreeSitter & LSP integration 

## features 
- tool logging
- cost tracking 
- memory & context handling 
- tree-sitter
- LSP integration 
- sandboxed execution of untrusted code.

## system prompt checking
- checks the current system prompts & trusted files like README.md, CLAUDE.md, CODEX.md, AGENTS.md for prompt poisoning 
- raises error, fails fast, fails safe
- runs once during startup 
- uses separate prompt so it cannot be influenced 
- returns structured response to identify poisoning 
- if the check reports critical issue or can't complete its analysis, main agent won't start. 
```
program starts
      │
      ▼
Locate project root
      │
      ▼
Collect instruction files
      │
      ▼
Create NEW scanner client
      │
      ▼
Send only:
    - scanner prompt
    - file contents
      │
      ▼
Receive structured ScanResult
      │
      ▼
safe?
 ├── yes → start agent
 └── no  → abort immediately
```
- another way to make sure that prompts are not getting poisoned is by checking file integrity using hashing & checking against the original SHA256 hash. 

## bash / shell tool research
- security measures required 
- prevent execution of harmful commands 
- prevent curl web access
- prevent execution of arbitary code in shell
- implement a subprocess based execution to prevent script / cmd outside the current working directory 
- agent's usage
- required for git commands 
- required to run python files (initially only python files)
- performing tests 
- performing lints
- searching using grep cmd
- file inspections - cat, head, tail, wc, ls, pwd
      - cat : print file content
      - head : first n lines of file 
      - tail : last n lines of file
      - wc : word count 
      - ls : list directories
      - pwd : print working directory 
- dependency inspection - uv list 
- environment information - python --version, 
- database interaction - sqlite3 (later)
- forbidden shell cmds 
      - tail -f 
      - rm
      - mv
      - cp 
      - chmod
      - chown
      - mount
      - ln 
      - sudo 
      - su
      - shutdown
      - reboot
      - systemctl 
      - service
      - pkill 
      - kill 
      - curl - exposed using a web search tool 
      - wget
      - scp
      - ssh
      - nc
      - telnet 
      - package installation : uv add, pip install, brew
      - process management : nohup, &, jobs, bg, fg, screen, tmux
- allowed commands / whitelist
      - git : status, diff, log, show, blame, branch
      - pytest : none
      - ruff : check, format 
      - ls
      - pwd
      - cat
- every cmd that agent executes is configured with shell=False, cwd= project_root, fixed timeout, output size limit 

## not implementing a shell tool
- agent may hallucinate and execute any shell tool 
- parsing and validation is a bit hard 
- would rather expose required tools as python function with proper parsing and validation for each tool 

## blacklisting vs whitelisting resources
- blacklisting can only help when you have an exhaustive list of things you want to avoid / prevent from being executed / conducted 
- whitelist approach helps to reduce the scope of resources that can be executed/ created/ so that only required things are performed & all other by default are restricted.
- whilelisting shell cmds - we may not know all the harmful/ dangerous shell cmds so instead we can whitelist only a few that we know are safe for our system in general

## what does git help with
- git diff - what changed - documentation & reasoning
- git log - to learn about recent work & find cause for bugs/ crashes - atleast a headstart
- git blame - so agent can reason the commit messages and understand why a line of code exists
- commit message are free documentation for code snippets
- reduced search space by targetted diff changes
- verify its own work git diff
- git restore - undo mistakes
- git bisect - regression, find out which commit introduced a bug 
- git diff - for code reviews
- git branches - for multi-agent workflows, each agent uses its own branch 

## typical git loop 
- git status 
- git diff
- understand changed files
- edit code 
- run tests
- git diff
- review own changes
- commit 

## features to be added later
- cost tracking
- context compaction when context limit is about to hit
- structured output validation 
- conversation history 
- saving session data 
- long term memory 
- user inclusion for permissions
- tool permission 
- blocking path other than the paths inside current directories
- whitelisting allowed commands 
- planning 
- orchestration 
- reflection 
- in-memory scratchpad for agent reasoning 
- pause & resume 
- security measures
- prompt injection vulnerability 
- prompt leakage
- tool permission boundary 
- input sanitization 
- secret and PII isolation 
- jailbreak detection 
- rate limiting
- incremental & surgical file edits to reduce token wastage
- observability 
- monitoring 
- agent traces
- undo / redo memory 
- git tools 
- agent evaluations 
