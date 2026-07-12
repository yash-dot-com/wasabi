# WASABI Project Summary
## Testing Overview
## Architecture
The architecture supports core agent functionalities, including tool execution and context management, while maintaining strict security on file system and repository interactions.

## Key Modules
- **Core Agent Loop:** Facilitates interaction between LLMs and tool execute calls.
- **Filesystem Tools:** Manage file operations with safety measures in place.
- **Git Tools:** Enables version control capabilities while protecting the project environment.
- **Dependency Management:** Handles project dependencies efficiently.
- **Enhanced Functionality:** Improved component ability to handle lazy generation and loading of context, enabling dynamic modifications as needed.

## Insertion Test
- `test command`: This is a test command inserted for mutation testing.
This section tests the insertion functionality of the file mutation tools.## Dependencies
- Python 3.x
- OpenAI API
- uv (virtual environment manager)
- Tree-sitter

## Entry Points
The main entry point is the `main.py` script, which initializes the agent and manages its execution flow. Commands are routed through this script to various functionalities in a controlled manner.

## Commands- `test command`: This is a test command inserted for mutation testing.
- `test command updated`: This command has been updated for further testing.
The following commands can be executed through the terminal:
- `uv sync`: Synchronizes virtual environment with dependencies.
- `uv add <package>`: Adds a Python package to the project.
- `uv remove <package>`: Removes a Python package from the project.

## Security Constraints
The design ensures project-root isolation and user permissions for sensitive operations. It implements various checks to prevent prompt injection, tool misuse, and unauthorized access to the host system.

## Engineering Decisions
- Enhanced validation and atomic file writing capabilities in the `Agent` class.
- Prioritized security and control over the agent's capabilities to mitigate risks.
- Developed an efficient context management strategy to minimize API usage costs.
- Employed Tree-sitter for enhanced code understanding and manipulation.
- Prioritized security and control over the agent's capabilities to mitigate risks.
- Developed an efficient context management strategy to minimize API usage costs.
- Employed Tree-sitter for enhanced code understanding and manipulation.

## Recent Changes
- feat(add wasabi.md): lazy generation and loading
- feat(WASABI.md): lazy load or generate WASABI.md on the fly when required for mutating projects.
- docs(README.md): updated scope of project
- docs(README.md): added todos