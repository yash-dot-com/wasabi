# WASABI Project Summary

## Overview
Wasabi is a Python terminal coding agent designed for exploring agentic systems, secure agent execution, and code intelligence alongside efficient context management. Focused on understanding how coding agents operate, it engages in multi-step workflows and controlled interactions with repositories.

## Architecture
The architecture supports core agent functionalities, including tool execution and context management, while maintaining strict security on file system and repository interactions.

## Key Modules
- **Core Agent Loop:** Facilitates interaction between LLMs and tool execute calls.
- **Filesystem Tools:** Manage file operations with safety measures in place.
- **Git Tools:** Enables version control capabilities while protecting the project environment.
- **Dependency Management:** Handles project dependencies efficiently.

## Dependencies
- Python 3.x
- OpenAI API
- uv (virtual environment manager)
- Tree-sitter

## Entry Points
The main entry point is the `main.py` script, which initializes the agent and manages its execution flow. Commands are routed through this script to various functionalities in a controlled manner.

## Commands
The following commands can be executed through the terminal:
- `uv sync`: Synchronizes virtual environment with dependencies.
- `uv add <package>`: Adds a Python package to the project.
- `uv remove <package>`: Removes a Python package from the project.

## Security Constraints
The design ensures project-root isolation and user permissions for sensitive operations. It implements various checks to prevent prompt injection, tool misuse, and unauthorized access to the host system.

## Engineering Decisions
- Prioritized security and control over the agent's capabilities to mitigate risks.
- Developed an efficient context management strategy to minimize API usage costs.
- Employed Tree-sitter for enhanced code understanding and manipulation.

This document serves as a durable context for future agent sessions, laying out crucial aspects of the Wasabi project.