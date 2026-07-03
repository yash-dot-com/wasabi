## roadmap 
- DONE : system diagnostics run - check for prompt injections, system poisoning : check src/system_check.py
- CURRENTLY WORKING ON : secure shell execution environment - implementing whitelisting vs blacklisting strategy
- git helper tools, see research & techniques in dedicated section below 
- surgical edits
- undo file - so that previous code can be recovered
- create single source of truth for code
- web search fn - to fetch new documentation 
- DONE: security measures - prevent edits in files other than current working directory 
- security measure - blacklisting harmful scripts execution
- security measure - ask user for permission while running scripts 
- tool - shell tool for executing scripts & reading their output from terminal 
- multi-agents task distribution and follow-up pipeline 
- background tasks 
- IMP : fix decision fatigue for agent by narrowing down and pin-pointing system prompt for better tool usage 
- IMP : build evaluation system for evaluating agent harness 
- REFACTOR : system security check 

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