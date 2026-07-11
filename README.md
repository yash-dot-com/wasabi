# Wasabi: A Cutting-Edge Engineering Project in the Agent Space

<p align="center">
  <img src="static/Wasabi-Header.png" width="1100" alt="Wasabi Logo">
</p>

## Overview

Wasabi is a Python-first coding agent focused on enhancing software project understanding and modification through a secure, streamlined interface. This document outlines the key features and engineering innovations achieved within this project, as well as a comprehensive overview of the tools available to the agent.

Wasabi is a Python-first coding agent focused on enhancing software project understanding and modification through a secure, streamlined interface. This document outlines the key features and engineering innovations achieved within this project.

## Core Capabilities

### Available Tools

The Wasabi agent is equipped with a suite of tools that enable efficient file and project management. These tools include:

1. **File Management Tools**:
   - **read_file**: Reads the contents of a specified file path.
   - **list_files**: Lists all files and directories in the specified path.
   - **edit_file**: Edits a file by replacing specified text, with the option to create a new file if it doesn't exist.
   - **delete_file**: Moves a specified file to a soft delete (trash) directory, allowing for recovery.
   - **restore_file**: Recovers a file from the trash directory to its original path.

2. **Git Tools**:
   - **git_diff**: Displays the differences for a particular file or the entire project.
   - **git_status**: Provides the current status of the Git repository, including modified and untracked files.
   - **git_log**: Displays a log of recent commits with the option to limit the number of entries.
   - **git_blame**: Shows the last modification timestamp and author for each line of a specified file.
   - **git_show**: Inspects a single Git commit by its hash.

3. **Python and Dependency Management Tools**:
   - **uv_sync**: Synchronizes the project's virtual environment with the specified dependency files.
   - **uv_add**: Adds specified Python packages to the project.
   - **uv_remove**: Removes specified Python packages from the project.
   - **uv_run_script**: Executes a specified Python script within the project’s virtual environment, with user permission required.
   - **uv_run_module**: Runs an importable Python module in the same environment.

4. **Search Tools**:
   - **search_text**: Searches for text across project files and returns the matching lines.
   - **find_files**: Locates files in the project based on filename or pattern.
   - **search_text_with_context**: Performs a search with added context lines for better understanding.

### Security Measures

To ensure the security of the coding agent, several measures are in place:
- **User Permissions**: Any action that could affect files or run scripts requires prior user approval, adding a layer of security to sensitive operations.
- **Project Root Checking**: Ensures that all operations remain within the project's root directory, preventing unauthorized access to the wider file system.

### 1. Security
- **Capability-Based Security**: Ensures that the agent operates within a defined scope, reducing the risk of unintended system manipulation.
- **User Approval Mechanism**: Users must approve any access requests for sensitive tools, adding an extra layer of security.
- **Sandbox Environment**: Restricts the agent's file system access to the project root, preventing any undesirable external operations.

### 2. Semantic Understanding
- **Tree-Sitter Integration**: This technology allows for deeper semantic analysis of code, improving comprehension and modification capabilities.
- **LSP Support**: The agent utilizes Language Server Protocol for real-time diagnostics and error correction, thereby improving coding accuracy and reducing bugs.

### 3. Precision in Code Changes
- **Surgical Edits**: Allows the agent to read and write precise portions of code, enhancing edit accuracy without affecting unrelated sections. This is implemented through targeted read and replace functions.
- **Incremental Context Updates**: The agent maintains and updates its understanding of the project context during operations, creating a smoother workflow.

### 4. Advanced File Discovery and Search
- **Ripgrep-Based Search**: Implements fast search capabilities for locating files and code snippets, greatly improving developer efficiency.
- **Structured Outputs**: Provides JSON formatted results from searches and operations for consistency and easy integration into further processes.

### 5. Phased Development
- The project is structured into defined phases focusing on building a functional coding agent, repository understanding, semantic intelligence, and context engine capabilities.
- **Future Enhancements**: Planned features, including multi-agent workspaces and intelligent editing, highlight the forward-thinking nature of the project.

## Future Improvements and Research Engineering

### 1. Self-Learning Capabilities
- **Global and Project-Specific Learning**: Developing a system that maintains lessons learned and project-specific knowledge which will enhance the agent's overall understanding and adaptability.

### 2. Cached Context Management
- **Cached Project Context**: Implementing a continuous caching mechanism that keeps track of project state and context, allowing the agent to quickly adapt to changes without reloading unnecessary information.
- **Context Compaction**: Improving algorithms for compacting context data, ensuring efficient memory use while preserving vital information needed for decision-making.

### 3. Precision in Code Handling and Token Optimization
- **Abstract Syntax Tree (AST) Graph**: Implementing a structured representation of the code through an AST graph, which allows for more efficient modifications and understanding of the code structure. This representation aids in reducing token usage during processing by focusing only on relevant code elements.
- **Precise Reads, Writes, and Edits**: Enhancing the agent's ability to perform focused changes to code, reducing token usage while maximizing the quality of edits made. This ensures that only relevant changes in the code are processed, improving efficiency and resource use.

### 4. Security Enhancements
- **Enhanced Security Measures**: Continuing to fortify the agent's security with rigorous checks and protections against vulnerabilities, particularly focusing on command execution and file interactions.
- **Dynamic Security Analysis**: Researching and developing new agent security methodologies to detect and mitigate vulnerabilities in real-time as they arise, ensuring a proactive stance against attacks.

### 5. Comprehensive Tool Integration
- **Extensive Tool Set**: Continuing to build and integrate capabilities for a variety of tools, including Git operations, Python testing frameworks, diagnostics, and semantic analysis tools to create a versatile coding environment.

### 6. Advanced Research on Agent Vulnerabilities
- **Proactive Security Research**: Engaging in ongoing research and development to identify potential vulnerabilities in future iterations of the code agent, ensuring resilience and reliability in diverse coding scenarios.

### 7. Observability and Training Enhancements
- **Improving Observability**: Enhancing the agent's monitoring capabilities to understand its behavior and decision-making processes better, fostering improved interactions and user experiences.

### 1. Continuous Enhancement of Security Features
- **Deeper Security Checks**: Implementing advanced checks to prevent prompt injections and agent poisoning.
- **Dynamic Approval Workflow**: Enabling more granular control and real-time monitoring of tool access requests.

### 2. Multi-Agent Collaboration
- **Intelligent Editing**: Developing capabilities for semantic edits instead of simple text replacements to ensure code refactoring and modifications are context-aware.
- **Task Distribution**: Creating an infrastructure where multiple agents collaboratively update documentation, manage dependencies, and handle repetitive tasks without user intervention.

### 3. Enhanced Context Management
- **Incremental Cache Invalidation**: Enhancing cache management algorithms to efficiently handle context updates during coding sessions while minimizing resource overhead.
- **Long-Term Memory Implementation**: Building features to retain user preferences and project-specific learnings across sessions for an improved user experience.

### 4. Advanced Features Development
- **Cost Tracking and Resource Management**: Integrating tools for monitoring resource consumption and providing insights to reduce overhead during development.
- **Observability and Monitoring**: Implementing traceability features within the coding agent to track its operations, performance, and security potential vulnerabilities.

### 5. Comprehensive Testing and Validation Strategy
- **Robust Unit and Integration Tests**: Expanding on existing tests to validate not just functionality but also security, flow, and performance in real-time scenarios.
- **Adversarial Test Cases**: Developing tests that challenge the robustness of the system against potential misuse and edge cases.

## Conclusion

Wasabi stands out in the agent space by integrating robust security measures, precision in code handling, and innovative search capabilities. This project pushes the boundaries of what coding agents can achieve in understanding and modifying software, reinforcing the importance of a secure, efficient coding environment.