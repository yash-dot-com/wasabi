import platform
import os
import hashlib
import tempfile
from dataclasses import dataclass, asdict
from pydantic import BaseModel
from typing import Callable, Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import subprocess
import time
from src.tools.security_tools.project_root_checker import check_project_root
from src.system_check import security_scan
from src.user_permission import user_permission
import json

load_dotenv()

@dataclass
class CommandResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int

# constants & env 
openai = os.getenv("OPENAI_API")
system_prompt_path = os.getenv("SYSTEM_PROMPT_PATH")
project_root = Path.cwd().resolve()
MAX_OUTPUT = 100_000 # for truncating stdout / stderr from subprocesses 
MAX_TOOL_CALLS_PER_TOOL = 5

def get_system_prompt(system_prompt_path: str):
    """ safely loads system instructions from specified file """
    if not system_prompt_path:
        raise RuntimeError("SYSTEM_PROMPT_PATH is not set.")

    try:
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError as e:
        raise RuntimeError(f"System prompt file not found: {str(e)}") from e
    except Exception as e:
        raise RuntimeError("Could not read the system prompt file.") from e

# 1 - create tool model
# standardized tool schema 
class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

# 2 - create agent class 
# agent class 
# use : colon for type annotation 
# use = for assigning values
class Agent:
    def __init__(
        self,
        api_key: str,
        system_prompt: str,
        event_handler: Optional[Callable[[Dict[str, Any]], None]] = None,
        permission_handler: Optional[Callable[[str, str], bool]] = None,
    ):
        self._api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.project_root = Path.cwd().resolve()
        # initialize messages array with system prompt for the agent.

        self.messages: List[Dict[str, Any]] = [
            {"role":"system", "content": system_prompt}
        ]
        self.tools: List[Tool] = []
        self._event_handler = event_handler or (lambda event: None)
        self._permission_handler = permission_handler or (lambda tool_name, command: False)
        self._project_context_loaded = False
        self._generating_project_context = False
        self._setup_tools()
        self._emit("status", message=f"Agent initialized with {len(self.tools)} tools")

    def _emit(self, event_type: str, **payload: Any) -> None:
        """Notify the host about progress without depending on terminal rendering."""
        self._event_handler({"type": event_type, **payload})

    def _request_permission(self, tool_name: str, command: str) -> bool:
        return user_permission(tool_name, command, self._permission_handler)

    def _get_project_root(self) -> str:
        return self.project_root.as_posix()
    
    def _project_context_path(self) -> Path:
        return self.project_root / "WASABI.md"

    def _get_file_hash(self, file_path: Path) -> str:
        """Return the SHA-256 hash of a file's current contents."""
        with open(file_path, "rb") as file:
            return hashlib.sha256(file.read()).hexdigest()

    def _validate_file_hash(self, file_path: Path, expected_hash: str) -> bool:
        current_hash = self._get_file_hash(file_path)
        return current_hash == expected_hash

    def _atomic_write(self, file_path: Path, content: str) -> None:
        temporary_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=file_path.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, file_path)
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _requires_project_context(user_input: str) -> bool:
        """Return whether a request needs repository knowledge beyond Git metadata."""
        normalized_input = user_input.lower()
        context_terms = (
            "architecture",
            "dependency",
            "dependencies",
            "module",
            "modules",
            "codebase",
            "repository",
            "project structure",
            "how does",
            "where is",
            "implement",
            "modify",
            "change",
            "fix",
            "refactor",
            "optimize",
            "configure",
            "add feature",
            "update",
        )
        return any(term in normalized_input for term in context_terms)

    def _ensure_project_context(self) -> str:
        """Load the saved context, generating it once when it does not exist."""
        context_path = self._project_context_path()
        if not context_path.exists():
            self._generate_project_context()

        context = self._load_project_context()
        self._project_context_loaded = True
        return context

    def _generate_project_context(self) -> None:
        """
        Invoke the agent internally with a specialized prompt to inspect
        the repository and create WASABI.md.
        """
        if self._generating_project_context:
            raise RuntimeError("Project-context generation is already in progress.")

        self._generating_project_context = True
        try:
            context_agent = Agent(
                self._api_key,
                self.messages[0]["content"],
                self._event_handler,
                self._permission_handler,
            )
            context_agent._generating_project_context = True
            context_agent.chat(
                "Create WASABI.md now. Inspect the repository with the available tools, "
                "then use edit_file to write a concise, durable project summary. Include "
                "the overview, architecture, key modules, dependencies, entry points, "
                "commands, security constraints, and engineering decisions. Do not copy "
                "source code, include chat history, or speculate."
            )
        finally:
            self._generating_project_context = False

        if not self._project_context_path().is_file():
            raise RuntimeError("The agent did not create WASABI.md while generating project context.")

    def _load_project_context(self) -> str:
        try:
            return self._project_context_path().read_text(encoding="utf-8").strip()
        except OSError as error:
            raise RuntimeError(f"Could not read WASABI.md: {error}") from error

        
    def _setup_tools(self):
        self.tools = [
            #4 - create tool description, not the actual tool. 
            Tool(
                name="read_file",
                description="read the contents of a file at the specified path",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "the path to the file to read"
                        }
                    },
                    "required": ["path"],
                    "additionalProperties": False 
                },
            ),

            Tool(
                name="read_lines",
                description=(
                    "Read an inclusive, 1-based line range from a file and return "
                    "line-numbered content, the current SHA-256 file hash, and total lines."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file, relative to the project root.",
                        },
                        "start_line": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "First line to read, using 1-based inclusive numbering.",
                        },
                        "end_line": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Last line to read, using 1-based inclusive numbering.",
                        },
                    },
                    "required": ["path", "start_line", "end_line"],
                    "additionalProperties": False,
                },
            ),

            Tool(
                name="list_files",
                description="list all files and directories in the specified path",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type":"string",
                            "description": "the directory path to list (defaults to current directory)"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="edit_file",
                description=(
                    "Create a new file with the supplied content. Do not use this tool to edit "
                    "an existing file; use replace_exact, insert_before, or insert_after instead."
                ),
                parameters={
                    "type":"object",
                    "properties": {
                        "path": {
                            "type":"string",
                            "description":"the path to the file to edit",
                        },
                        "old_text": {
                            "type": "string",
                            "description": "The text to search for and replace (leave empty to create new file)"
                        },
                        "new_text": {
                            "type": "string",
                            "description": "The text to replace old_text with"
                        }
                    },
                    "required": ["path","new_text"],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="replace_exact",
                description=(
                    "Atomically replace one unique exact text block in an existing file after "
                    "confirming its SHA-256 hash matches a prior read_lines result."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path relative to the project root."},
                        "expected_hash": {
                            "type": "string",
                            "pattern": "^[a-f0-9]{64}$",
                            "description": "SHA-256 hash returned by read_lines for this file.",
                        },
                        "old_content": {
                            "type": "string",
                            "description": "The unique, exact text block to replace.",
                        },
                        "new_content": {
                            "type": "string",
                            "description": "Replacement text inserted verbatim.",
                        },
                    },
                    "required": ["path", "expected_hash", "old_content", "new_content"],
                    "additionalProperties": False,
                },
            ),

            Tool(
                name="replace_lines",
                description=(
                    "Atomically replace an inclusive 1-based line range in an existing file after "
                    "confirming its SHA-256 hash matches a prior read_lines result."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path relative to the project root."},
                        "expected_hash": {
                            "type": "string",
                            "pattern": "^[a-f0-9]{64}$",
                            "description": "SHA-256 hash returned by read_lines for this file.",
                        },
                        "start_line": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "First line to replace, using 1-based inclusive numbering.",
                        },
                        "end_line": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Last line to replace, using 1-based inclusive numbering.",
                        },
                        "replacement": {
                            "type": "string",
                            "description": "Replacement text inserted verbatim.",
                        },
                    },
                    "required": ["path", "expected_hash", "start_line", "end_line", "replacement"],
                    "additionalProperties": False,
                },
            ),

            Tool(
                name="insert_before",
                description=(
                    "Atomically insert text verbatim before one unique exact anchor in an existing "
                    "file after confirming its SHA-256 hash matches a prior read_lines result."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path relative to the project root."},
                        "expected_hash": {
                            "type": "string",
                            "pattern": "^[a-f0-9]{64}$",
                            "description": "SHA-256 hash returned by read_lines for this file.",
                        },
                        "anchor": {"type": "string", "description": "The unique, exact anchor text."},
                        "new_content": {"type": "string", "description": "Text inserted verbatim."},
                    },
                    "required": ["path", "expected_hash", "anchor", "new_content"],
                    "additionalProperties": False,
                },
            ),

            Tool(
                name="insert_after",
                description=(
                    "Atomically insert text verbatim after one unique exact anchor in an existing "
                    "file after confirming its SHA-256 hash matches a prior read_lines result."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path relative to the project root."},
                        "expected_hash": {
                            "type": "string",
                            "pattern": "^[a-f0-9]{64}$",
                            "description": "SHA-256 hash returned by read_lines for this file.",
                        },
                        "anchor": {"type": "string", "description": "The unique, exact anchor text."},
                        "new_content": {"type": "string", "description": "Text inserted verbatim."},
                    },
                    "required": ["path", "expected_hash", "anchor", "new_content"],
                    "additionalProperties": False,
                },
            ),

            Tool(
                name="get_project_root",
                description="get the path for current working directory",
                parameters={},
            ),

            Tool(
                name="ensure_project_context",
                description=(
                    "Load the durable WASABI.md project context, generating it only when "
                    "the file does not exist. Use when repository context is needed."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                },
            ),

            Tool(
                name="load_project_context",
                description=(
                    "Load and return the existing WASABI.md project context. Use only "
                    "when the file is known to exist; this tool never generates or edits it."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                },
            ),

            Tool(
                name="generate_project_context",
                description=(
                    "Inspect the repository and create WASABI.md when it is missing. "
                    "This tool does not overwrite an existing context file."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                },
            ),

            Tool(
                name="delete_file",
                description="move a file to ./wasabi/trash for deletion, basically soft delete to enable recovery",
                parameters={
                    "type":"object",
                    "properties": {
                        "file_path": {
                            "type":"string",
                            "description":"required. path of the file that needs to be moved to trash"
                        }
                    },
                    "required":["file_path"],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="git_diff",
                description="get diffs for a particular file, by default whole project",
                parameters={
                    "type":"object",
                    "properties": {
                        "file_path": {
                            "type":"string",
                            "description":"optional. Relative path to a file within the project root, path of the file to view changes in that particular file"
                        }
                    },
                    "required":[],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="restore_file",
                description="move a file from ./wasabi/trash to its original path, restore a file from trash",
                parameters={
                    "type":"object",
                    "properties": {
                        "file_path": {
                            "type":"string",
                            "description":"path of the file that needs to be recovered"
                        }
                    },
                    "required":["file_path"],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="git_blame",
                description="get blame for a file specified by file_path",
                parameters={
                    "type":"object",
                    "properties": {
                        "file_path": {
                            "type":"string",
                            "description":"path of the file for which you need to acquire the blame history"
                        }
                    },
                    "required":["file_path"],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="git_status",
                description="Get the current Git repository status, purpose : Understand repository history and changes." 
                + "Current branch, Modified files, Staged files, Untracked files",
                parameters={}
            ),

            Tool(
                name="uv_sync",
                description="Synchronizes the project's virtual environment with pyproject.toml and uv.lock, installs necessary and removes unnecessary ones",
                parameters={}
            ),

            Tool(
                name="uv_version",
                description="get version for uv tool",
                parameters={}
            ),

            Tool(
                name="uv_add",
                description="add python packages to project using uv",
                parameters={
                    "type":"object",
                    "properties": {
                        "package_names": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of Python package names to add to the project."
                        }
                    },
                    "required":["package_names"],
                    "additionalProperties":False
                }
            ),

            Tool(
                name="uv_remove",
                description="remove python packages from project using uv",
                parameters={
                    "type":"object",
                    "properties": {
                        "package_names": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of Python package names to be removed from the project."
                        }
                    },
                    "required":["package_names"],
                    "additionalProperties":False
                }
            ),

            Tool(
                name="uv_run_script",
                description=(
                    "Run a specific Python script file inside the project's uv-managed "
                    "environment. Use this when a Python file such as main.py, script.py, "
                    "or scripts/setup.py needs to be executed. The user will be asked for "
                    "permission before execution. Do not use this tool to bypass denied "
                    "operations, security restrictions, or dedicated tools."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "script_path": {
                            "type": "string",
                            "description": (
                                "Path to the Python script to execute, relative to the "
                                "project root. Example: 'main.py' or 'scripts/setup.py'."
                            )
                        },
                        "arguments": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": (
                                "Optional command-line arguments passed directly to the "
                                "Python script. Example: ['--verbose', '--port', '8000']."
                            )
                        }
                    },
                    "required": ["script_path"],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="uv_run_module",
                description=(
                    "Run an importable Python module using 'python -m' inside the project's "
                    "uv-managed environment. Use this for modules designed to be executed "
                    "through Python's module system, such as pytest or project modules. "
                    "The user will be asked for permission before execution. Do not use "
                    "this tool to bypass script execution restrictions, denied operations, "
                    "or other security boundaries."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "module_name": {
                            "type": "string",
                            "description": (
                                "Fully qualified importable Python module name to execute. "
                                "Examples: 'pytest', 'http.server', or 'package.module'."
                            )
                        },
                        "arguments": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": (
                                "Optional command-line arguments passed to the module. "
                                "Example: ['tests/', '-v']."
                            )
                        }
                    },
                    "required": ["module_name"],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="uv_run_command",
                description=(
                    "Run a command-line executable available inside the project's "
                    "uv-managed environment. Use this for development tools such as pytest, "
                    "ruff, mypy, or other legitimate project CLI commands. The user will "
                    "be asked for permission before execution. Never use this tool to run "
                    "shell interpreters, destructive system commands, chain commands, "
                    "perform command substitution, or bypass denied operations and security "
                    "restrictions. Prefer dedicated tools whenever one exists."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": (
                                "Name of the executable to run. Examples: 'pytest', "
                                "'ruff', or 'mypy'. Do not include arguments in this field."
                            )
                        },
                        "arguments": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": (
                                "Optional arguments passed directly to the executable. "
                                "Example for 'ruff': ['check', '.']. Example for 'pytest': "
                                "['tests/', '-v']."
                            )
                        }
                    },
                    "required": ["command"],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="git_diff_summary",
                description="get a quick statistic summary of all the changed files.",
                parameters={}
            ),

            Tool(
                name="uv_project_dependency_tree",
                description="get quick project's dependency tree",
                parameters={}
            ),

            Tool(
                name="system_info",
                description="get information about operating system, python version, uv version, project root",
                parameters={}
            ),

            Tool(
                name="git_log",
                description="view one-line log of commits with commit hashes, commits hashes from this command can be used with git show and other tools recursively to perform complex actions.",
                parameters={
                    "type":"object",
                    "properties": {
                        "limit": {
                            "type":"integer",
                            "description":"Optional. Numeric limit to control the number of commits listed by the command."
                        }
                    },
                    "required":[],
                    "additionalProperties":False
                }
            ),

            Tool(
                name="git_show",
                description="inspect single git commit with its commit hash; returns : author details, date of commit, diff, & commit message, extremely useful when you want to understand why something changed",
                parameters={
                    "type":"object",
                    "properties": {
                        "commit_hash": {
                            "type":"string",
                            "description":"Required. string form of the commit hash of the commit which is supposed to be inspected."
                        }
                    },
                    "required":["commit_hash"],
                    "additionalProperties":False
                }
            ),

            Tool(
                name="search_text",
                description=(
                    "Search for text across files in the project using ripgrep. "
                    "Use this tool to locate where a function, class, variable, string, "
                    "configuration value, error message, or any other text appears in the codebase. "
                    "Returns the matching file path, exact line number, and matched line content. "
                    "Use the returned file path and line number with precise read tools to inspect "
                    "the relevant code instead of reading entire files unnecessarily."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "The text or pattern to search for across project files. "
                                "Examples: 'user_permission', 'class Agent', or 'TODO'."
                            )
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="find_files",
                description=(
                    "Find files in the current project by filename or glob pattern using ripgrep. "
                    "Use this tool to discover files when you know the filename, extension, naming "
                    "pattern, or approximate file type but not the exact path. It respects the "
                    "project's .gitignore rules by default and returns matching file paths. "
                    "Examples include finding all Python files with '*.py', test files with "
                    "'test_*.py', configuration files with 'pyproject.toml', or files inside a "
                    "specific directory with 'src/*.py'. Use this tool for file discovery; use "
                    "search_text when searching for content inside files."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": (
                                "Filename or glob pattern used to find matching files. "
                                "Examples: '*.py', 'test_*.py', 'pyproject.toml', "
                                "'src/*.py', or '**/test_*.py'."
                            )
                        }
                    },
                    "required": ["pattern"],
                    "additionalProperties": False
                }
            ),

            Tool(
                name="search_text_with_context",
                description=(
                    "Search for text across project files using ripgrep and return each matching "
                    "line together with surrounding lines for additional context. Use this when "
                    "you need to understand nearby code around a search result without reading "
                    "the entire file. The search is case-insensitive and returns file paths, "
                    "line numbers, matching lines, and the requested number of lines before and "
                    "after each match."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "search_string": {
                            "type": "string",
                            "description": (
                                "The text or pattern to search for across project files. "
                                "Examples: 'user_permission', 'class Agent', or 'TODO'."
                            )
                        },
                        "context_length": {
                            "type": "integer",
                            "minimum": 0,
                            "description": (
                                "Number of surrounding lines to return before and after each "
                                "matching line. For example, 5 returns up to 5 lines before "
                                "and 5 lines after every match."
                            )
                        }
                    },
                    "required": ["search_string", "context_length"],
                    "additionalProperties": False
                }
            )

        ]

    # 7 - cmd executor function 
    # tool -> git / python3 / uv / etc 
    # arguments -> flags & options.
    # the agent doesn't have 
    def _run_command(self, tool: str, args: list[str]) -> CommandResult:
        allowed_tools = ["git", "python3", "uv", "rg", "find"]

        # need to scope permission prompt only for destructive cmds / tools
        # if user_permission(tool, "") != True:
        #     return f"User Permission Denied"

        if tool not in allowed_tools:
            return f"ERROR : access denied; only git, python3, uv, rg, find are accessible"
        
        try:
            result = subprocess.run(
                [tool, *args],
                cwd=project_root,
                shell=False,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            stdout = result.stdout
            stderr = result.stderr

            if len(stdout) > MAX_OUTPUT:
                stdout = stdout[:MAX_OUTPUT] + "\n\n... OUTPUT TRUNCATED ..."

            if len(stderr) > MAX_OUTPUT:
                stderr = stderr[:MAX_OUTPUT] + "\n\n... OUTPUT TRUNCATED ..."

            return json.dumps(asdict(CommandResult(
                success=result.returncode == 0,
                stdout=stdout.strip(),
                stderr=stderr.strip(),
                exit_code=result.returncode,
            )))

        except subprocess.TimeoutExpired:

            return json.dumps(asdict(CommandResult(
                success=False,
                stdout="",
                stderr="Git command timed out.",
                exit_code=-1,
            )))

        except Exception as e:

            return json.dumps(asdict(CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
            )))
        
    # GIT TOOLS
    def _git_status(self):
        """
        Get the current Git repository status.

        Returns:
            Current branch, modified files,
            staged files and untracked files.
        """

        subprocess_result = self._run_command("git",["status", "--short", "--branch"])
        return subprocess_result
    
    def _git_diff(self, path: str=None):
        """
        get diffs for a particular file, by default whole project
        returns diff output.
        """
        options = ["diff"]
        if path:
            options.append(path)

        subprocess_result = self._run_command("git", options)
        return subprocess_result
    
    # replaced by diff summary function
    # def _git_changed_files(self):
    #     """
    #     returns names of files that have changes since the last commit
    #     """
    #     subprocess_result = self._run_command("git", ["diff", "--name-only", "-w", "--stat"])
    #     return subprocess_result
    
    def _git_log(self, limit: str = "20"):
        """
        view one line log of the current repository
        can also be used to get the git hash for commit to inspect a single commit with its author, date, diff
        """
        options = ["log", "--oneline", f"-{limit}"] 
        subprocess_result = self._run_command("git", options)
        return subprocess_result
    
    def _git_show(self, commit_hash: str):
        """
        requires : commit_hash : string
        inspect single git commit with its commit hash
        returns : author details, date of commit, diff, & commit message.
        """
        options = [
            "show",
            f"{commit_hash}"
        ]

        subprocess_result = self._run_command("git", options)
        return subprocess_result
    
    def _git_diff_summary(self):
        """
        quick diff views, shows no of lines changed across all the changed files
        """

        subprocess_result = self._run_command("git", ["diff", "--stat"])
        return subprocess_result
    
    def _git_blame(self, file_path: str):
        """
        last modification in file a specific file 
        """
        options = [
            "blame",
            f"{file_path}"
        ]

        subprocess_result = self._run_command("git",options)
        return subprocess_result
    
    def _system_info(self):
        """
        returns os, cwd, project root, python version, git version, uv version, rg version
        """

        platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "mac_ver": platform.mac_ver()
        }

        python_info = {
            "python" : platform.python_version(),
            "python_compiler" : platform.python_compiler()
        }

        uv_info = {
            "uv_version": self._run_command("uv", ["--version"]) 
        }

        result = json.dumps([platform_info, python_info, uv_info, str(project_root)])
        return result
    
    # UV TOOLS
    # tool description added for : uv project dependency tree
    # version, sync, add and remove 
    def _uv_project_dependency_tree(self):
        """
        returns the dependency tree for current working directory
        """
        subprocess_result = self._run_command("uv", ["tree"])
        return subprocess_result
    
    def _uv_version(self):
        subprocess_result = self._run_command("uv", ["--version"])
        return subprocess_result
    
    def _uv_sync(self):
        """
        Synchronizes the project's virtual environment with pyproject.toml and uv.lock. 
        Installs missing dependencies and removes unnecessary ones.
        """
        subprocess_result = self._run_command("uv", ["sync"])
        return subprocess_result
    
    # add in tool description and executor 
    def _uv_add(self, package_names: list[str]) -> str:
        """
        add single package or multiple packages to the project
        """
        if not package_names:
            return "No packages provided."

        packages = " ".join(package_names)

        if not self._request_permission("uv add", packages):
            return "User permission denied."

        options = [
            "add",
            *package_names,
        ]

        return self._run_command("uv", options)
    
    # add in tool description and executor
    def _uv_remove(self, package_names: list[str]):
        """
        remove single package or multiple packages from the project
        """

        if not package_names:
            return "No Packages provided"
        
        packages = " ".join(package_names)

        if not self._request_permission("uv remove", packages):
            return "User Permission Denied"
        
        options = [
            "remove",
            *package_names
        ]

        return self._run_command("uv", options)
    
    def _uv_lock(self):
        """
        Generates or updates uv.lock, resolving exact dependency versions. 
        Useful after dependency changes to ensure reproducible installations.
        """

        if not self._request_permission("uv", "lock"):
            return f"User Permission Denied"
        
        subprocess_result = self._run_command("uv", ["lock"])
        return subprocess_result
    
    def _uv_run_script(self, script_path: str, arguments: Optional[list[str]] = None):
        """
        runs a specific python script 
        """
        arguments = arguments or []

        if not self._request_permission(
            "Run Python script",
            f"{script_path} {' '.join(arguments)}",
        ):
            return "User permission denied."

        options = [
            "run",
            script_path,
            *arguments,
        ]

        return self._run_command("uv", options)
    
    def _uv_run_module(self, module_name: str, arguments: Optional[list[str]]= None):
        """
        run an importable python module
        """
        arguments = arguments or []

        if not self._request_permission(
            "Run Python module",
            f"{module_name} {' '.join(arguments)}",
        ):
            return "User permission denied."

        options = [
            "run",
            "python",
            "-m",
            module_name,
            *arguments,
        ]

        return self._run_command("uv", options)
    
    def _uv_run_command(self, command: str, arguments: Optional[list[str]]= None):
        """
        run command line tools like mypy, ruff, pytests
        """
        arguments = arguments or []

        if not self._request_permission(
            "Run command",
            f"{command} {' '.join(arguments)}",
        ):
            return "User permission denied."

        options = [
            "run",
            command,
            *arguments,
        ]

        return self._run_command("uv", options)
    
    # 5 - create tools for the agent here
    def _read_file(self, path: str) -> str:
        path = check_project_root(path)

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return f"Contents of {path}: \n {content}"
        except FileNotFoundError as e:
            return f"File not found: {path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _read_lines(self, path: str, start_line: int, end_line: int) -> str:
        file_path = check_project_root(path)

        if not file_path.is_file():
            raise RuntimeError(f"File not found: {file_path}")
        if start_line < 1 or end_line < start_line:
            raise RuntimeError("Invalid line range: start_line must be at least 1 and no greater than end_line.")

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise RuntimeError(f"Could not read file: {error}") from error

        total_lines = len(lines)
        if end_line > total_lines:
            raise RuntimeError(
                f"Invalid line range: {file_path} has {total_lines} lines, but end_line is {end_line}."
            )

        file_hash = self._get_file_hash(file_path)

        return json.dumps({
            "path": file_path.relative_to(self.project_root).as_posix(),
            "start_line": start_line,
            "end_line": end_line,
            "file_hash": file_hash,
            "total_lines": total_lines,
            "content": [
                {"line": line_number, "text": line}
                for line_number, line in enumerate(lines[start_line - 1:end_line], start=start_line)
            ],
        })
        
    def _list_files(self, path: str) -> str:
        path = check_project_root(path)

        try:
            if not os.path.exists(path):
                return f"path not found: {path}"
            
            items = []

            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)

                if os.path.isdir(item_path):
                    items.append(f"[DIR] {item}/")
                else:
                    items.append(f"[FILE] {item}")

            if not items:
                return f"empty directory {path}"
            
            return f"contents of {path}:\n" + "\n".join(items)
        except Exception as e:
            # returning errors as string for LLM to understand and reason next step.
            return f"Error listing the files: {str(e)}"
        
    def _delete_file(self, file_path: str) -> str:
        if not self._request_permission("delete file", file_path):
            return f"User Permission Denied"
        
        try:
            file_path = Path(file_path)
            resolved = (project_root / file_path).resolve()
            trash_path = (project_root / "./wasabi" / "trash")

            if not resolved.exists():
                return f"ERROR : file doesn't exists"
            
            if resolved.is_relative_to(trash_path):
                return f"ERROR : file is already in trash"

            if not resolved.is_relative_to(project_root):
                return f"ERROR : file deletion outside the root working directory is forbidden"
            
            if resolved == project_root:
                return f"ERROR : deleting project root is forbidden"
            
            if resolved.is_dir():
                return f"ERROR : directory deletion is forbidden"
            
            if resolved.is_symlink():
                return f"ERROR : symlink detected, deletion is forbidden"
            
            # if all passed, we can move the file to trash instead of permanently deleting it 


            trash_path.mkdir(parents=True, exist_ok=True)

            # to maintain original structure of file we find relative path of file to root 
            relative_file_path = resolved.relative_to(project_root)

            destination_in_trash = trash_path/relative_file_path
            destination_in_trash.parent.mkdir(parents=True, exist_ok=True)

            resolved.rename(destination_in_trash)

            return f"file {resolved} moved to {destination_in_trash} as {relative_file_path}"
        except PermissionError as e:
                return f"ERROR: Permission denied {str(e)}"

        except OSError as e:
                return f"ERROR: {str(e)}"

        except Exception as e:
                return f"ERROR: Unexpected error: {str(e)}"
        
    def _restore_file(self, file_path: str) -> str:
        try:
            file_path = Path(file_path)
            trash_root = project_root / "wasabi" / "trash"

            # create file path relative to trash bin 
            trash_path = project_root / "wasabi" / "trash" / file_path

            if not trash_path.exists():
                return f"ERROR : file not in trash can"
            
            original_relative_path = trash_path.relative_to(trash_root)

            destination = project_root / original_relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)

            trash_path.rename(destination)
            return f"{file_path} moved from {trash_path} to {destination}"
        except Exception as e:
            return f"ERROR : {str(e)}"
        

    def _edit_file(self, path: str, old_text: str, new_text: str) -> str:
        file_path = check_project_root(path)

        try:
            if file_path.exists():
                return (
                    "Existing file edits require replace_exact, replace_lines, insert_before, or insert_after "
                    "with a hash returned by read_lines."
                )

            file_path.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_write(file_path, new_text)
            return f"successfully created path: {file_path}"
        except Exception as e:
            return f"Error editing file: {str(e)}"

    def _modify_file(
        self,
        path: str,
        expected_hash: str,
        operation: str,
        mutation: Callable[[str], str],
    ) -> str:
        file_path = check_project_root(path)
        try:
            if not file_path.is_file():
                raise RuntimeError(f"File not found: {file_path}")
            if not self._validate_file_hash(file_path, expected_hash):
                raise RuntimeError("File changed since it was read. Call read_lines again before editing.")

            with open(file_path, "r", encoding="utf-8", newline="") as file:
                updated_content = mutation(file.read())
            self._atomic_write(file_path, updated_content)
            return self._surgical_mutation_result(file_path, operation)
        except OSError as error:
            raise RuntimeError(f"Could not read file: {error}") from error

    @staticmethod
    def _require_unique_match(content: str, target: str, target_name: str) -> None:
        if not target:
            raise RuntimeError(f"{target_name} must not be empty.")

        match_count = content.count(target)
        if match_count == 0:
            raise RuntimeError(f"Exact {target_name} was not found in the file.")
        if match_count > 1:
            raise RuntimeError(f"Exact {target_name} is ambiguous; it appears {match_count} times.")

    def _surgical_mutation_result(self, file_path: Path, operation: str) -> str:
        return json.dumps({
            "success": True,
            "operation": operation,
            "path": file_path.relative_to(self.project_root).as_posix(),
            "file_hash": self._get_file_hash(file_path),
        })

    def _replace_exact(
        self,
        path: str,
        expected_hash: str,
        old_content: str,
        new_content: str,
        operation: str = "replace_exact",
    ) -> str:
        def replace(content: str) -> str:
            self._require_unique_match(content, old_content, "old_content")
            return content.replace(old_content, new_content, 1)

        return self._modify_file(path, expected_hash, operation, replace)

    def _replace_lines(
        self,
        path: str,
        expected_hash: str,
        start_line: int,
        end_line: int,
        replacement: str,
    ) -> str:
        def replace(content: str) -> str:
            lines = content.splitlines(keepends=True)
            if start_line < 1 or end_line < start_line:
                raise RuntimeError(
                    "Invalid line range: start_line must be at least 1 and no greater than end_line."
                )
            if end_line > len(lines):
                raise RuntimeError(
                    f"Invalid line range: file has {len(lines)} lines, but end_line is {end_line}."
                )

            lines[start_line - 1:end_line] = [replacement] if replacement else []
            return "".join(lines)

        return self._modify_file(path, expected_hash, "replace_lines", replace)

    def _insert_before(
        self,
        path: str,
        expected_hash: str,
        anchor: str,
        new_content: str,
    ) -> str:
        return self._replace_exact(
            path,
            expected_hash,
            anchor,
            f"{new_content}{anchor}",
            operation="insert_before",
        )

    def _insert_after(
        self,
        path: str,
        expected_hash: str,
        anchor: str,
        new_content: str,
    ) -> str:
        return self._replace_exact(
            path,
            expected_hash,
            anchor,
            f"{anchor}{new_content}",
            operation="insert_after",
        )
        
    # searching text 
    def _search_text(self, search_string: str):
        options = [
            "-n",
            "-i",
            search_string
        ]
        subprocess_result = self._run_command("rg", options)
        
        if not subprocess_result:
            return []
        
        return subprocess_result
    
    def _search_text_with_context(self, search_string: str, context_length: int):
        options = [
            "-n",
            "-i",
            "-C",
            f"{context_length}",
            search_string
        ]
        subprocess_result = self._run_command("rg", options)

        if not subprocess_result:
            return []
        
        return subprocess_result

    # searching files 
    def _search_file(self, pattern: str):
        """
        rg --files -g pattern
        search for files with patterns
        """
        options = [
            "--files",
            "-g",
            pattern
        ]

        subprocess_result = self._run_command("rg", options)
        if not subprocess_result:
            return []
        
        return subprocess_result


    def _execute_tools(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """ try-catch block for executing tools selected by the agent using conditions """
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "read_lines":
                return self._read_lines(
                    tool_input["path"],
                    tool_input["start_line"],
                    tool_input["end_line"],
                )
            elif tool_name == "list_files":
                return self._list_files(tool_input.get("path", "."))
            elif tool_name == "edit_file":
                return self._edit_file(
                    tool_input["path"],
                    tool_input.get("old_text", ""),
                    tool_input["new_text"]
                )
            elif tool_name == "replace_exact":
                return self._replace_exact(
                    tool_input["path"],
                    tool_input["expected_hash"],
                    tool_input["old_content"],
                    tool_input["new_content"],
                )
            elif tool_name == "replace_lines":
                return self._replace_lines(
                    tool_input["path"],
                    tool_input["expected_hash"],
                    tool_input["start_line"],
                    tool_input["end_line"],
                    tool_input["replacement"],
                )
            elif tool_name == "insert_before":
                return self._insert_before(
                    tool_input["path"],
                    tool_input["expected_hash"],
                    tool_input["anchor"],
                    tool_input["new_content"],
                )
            elif tool_name == "insert_after":
                return self._insert_after(
                    tool_input["path"],
                    tool_input["expected_hash"],
                    tool_input["anchor"],
                    tool_input["new_content"],
                )
            elif tool_name == "get_project_root":
                return self._get_project_root()
            elif tool_name == "ensure_project_context":
                return self._ensure_project_context()
            elif tool_name == "load_project_context":
                project_context = self._load_project_context()
                self._project_context_loaded = True
                return project_context
            elif tool_name == "generate_project_context":
                if self._project_context_path().exists():
                    return "WASABI.md already exists; use load_project_context instead."
                self._generate_project_context()
                project_context = self._load_project_context()
                self._project_context_loaded = True
                return project_context
            elif tool_name == "delete_file":
                return self._delete_file(tool_input["file_path"])
            elif tool_name == "restore_file":
                return self._restore_file(tool_input["file_path"])
            elif tool_name == "git_status":
                return self._git_status()
            elif tool_name == "git_diff":
                return self._git_diff(tool_input.get("file_path"))
            # elif tool_name == "git_changed_file":
            #     return self._git_changed_file()
            elif tool_name == "git_log":
                return self._git_log(tool_input.get("limit", "20"))
            elif tool_name == "git_show":
                return self._git_show(tool_input["commit_hash"])
            elif tool_name == "git_diff_summary":
                return self._git_diff_summary()
            elif tool_name == "git_blame":
                return self._git_blame(tool_input["file_path"])
            elif tool_name == "uv_project_dependency_tree":
                return self._uv_project_dependency_tree()
            elif tool_name == "system_info":
                return self._system_info()
            elif tool_name == "uv_sync":
                return self._uv_sync()
            elif tool_name == "uv_version":
                return self._uv_version()
            elif tool_name == "uv_add":
                return self._uv_add(tool_input["package_names"])
            elif tool_name == "uv_remove":
                return self._uv_remove(tool_input["package_names"])
            elif tool_name == "uv_run_script":
                return self._uv_run_script(
                    tool_input["script_path"],
                    tool_input.get("arguments")
                )
            elif tool_name == "uv_run_module":
                return self._uv_run_module(
                    tool_input["module_name"],
                    tool_input.get("arguments")
                )
            elif tool_name == "uv_run_command":
                return self._uv_run_command(
                    tool_input["command"],
                    tool_input.get("arguments")
                )
            elif tool_name == "search_text":
                return self._search_text(tool_input["query"])
            elif tool_name == "find_files":
                return self._search_file(tool_input["pattern"])
            elif tool_name == "search_text_with_context":
                return self._search_text_with_context(
                    tool_input["search_string"],
                    tool_input["context_length"]
                )
            else:
                return f"unknown tool: {tool_name}, choose from specified tools only."
        except ValueError as e:
            return f"Access outside the project root is forbidden"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
        
    def get_openai_tools_payload(self) -> List[Dict[str, Any]]:
        """ converts the tools configurations into openai specified array format """
        return [
            {
                "type": "function",
                "function": {
                    "name" : tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.tools
        ]
    
    def chat(self, user_input: str) -> str:
        """ core execution loop for the agent to chat and execute tools """

        if (
            not self._project_context_loaded
            and not self._generating_project_context
            and self._requires_project_context(user_input)
        ):
            project_context = self._ensure_project_context()
            self.messages.append({
                "role": "system",
                "content": f"Project context from WASABI.md:\n\n{project_context}",
            })

        self.messages.append({"role": "user", "content": user_input})

        # function to create array of tool description as per openai SDK requirement
        tools_schema = self.get_openai_tools_payload()
        tool_call_counts: Dict[str, int] = {}

        while True:
            # request a response from LLM 
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages,
                tools=tools_schema,
                tool_choice="auto"
            )

            # extract raw assistant messages object
            assistant_message = response.choices[0].message

            # extract structural tool calls request by LLM 
            tool_calls = assistant_message.tool_calls

            if tool_calls:
                # append the tool call metadata as history 
                self.messages.append(assistant_message)
                limited_tools: set[str] = set()

                # iterate over each requested tool call 
                for tool_call in tool_calls:
                    call_id = tool_call.id
                    tool_name = tool_call.function.name

                    # extract the tool call argument into dictionary
                    tool_input = json.loads(tool_call.function.arguments)

                    self._emit("tool_call", tool_name=tool_name, arguments=tool_input, status="running")
                    started_at = time.perf_counter()

                    tool_call_counts[tool_name] = tool_call_counts.get(tool_name, 0) + 1
                    if tool_call_counts[tool_name] > MAX_TOOL_CALLS_PER_TOOL:
                        limited_tools.add(tool_name)
                        execution_result = (
                            f"Error: {tool_name} exceeded the per-request limit of "
                            f"{MAX_TOOL_CALLS_PER_TOOL} calls. Stop retrying this tool and report "
                            "the blocker to the user."
                        )
                    else:
                        execution_result = self._execute_tools(tool_name, tool_input)

                    failed = execution_result.lower().startswith(("error", "file not found"))

                    self._emit(
                        "tool_result",
                        tool_name=tool_name,
                        status="failed" if failed else "completed",
                        result=execution_result,
                        duration_seconds=time.perf_counter() - started_at,
                    )

                    # append the tool execution result to conversation memory 
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": tool_name,
                        "content": execution_result
                    })

                    # continue execution of further tools
                    continue 

                if limited_tools:
                    limited_tool_names = ", ".join(sorted(limited_tools))
                    message = (
                        f"Stopped because the per-request tool-call limit ({MAX_TOOL_CALLS_PER_TOOL}) "
                        f"was exceeded for: {limited_tool_names}."
                    )
                    self.messages.append({"role": "assistant", "content": message})
                    return message
            else:
                self.messages.append({"role":"assistant", "content":assistant_message.content})
                return assistant_message.content

  
def main() -> None:
    """Compose the existing agent with the terminal CLI presentation layer."""
    from src.cli.app import WasabiCLI

    project_root = Path.cwd().resolve()
    api_key = os.environ.get("OPENAI_API")
    prompt_file_path = os.environ.get("SYSTEM_PROMPT_PATH")

    startup_error: Optional[str] = None
    startup_status: Optional[str] = None
    agent_factory = None

    try:
        if not api_key:
            raise RuntimeError("OPENAI_API is not set.")

        prompt = get_system_prompt(prompt_file_path)
        scan_result = security_scan(project_root=project_root)
        if not scan_result.get("safe"):
            raise RuntimeError(
                "Startup security scan found potential vulnerabilities:\n"
                + json.dumps(scan_result, indent=2)
            )

        startup_status = "Ready · startup security scan passed"

        def agent_factory(event_handler, permission_handler):
            return Agent(api_key, prompt, event_handler, permission_handler)
    except Exception as error:
        startup_error = str(error)

    WasabiCLI(
        agent_factory=agent_factory,
        startup_error=startup_error,
        startup_status=startup_status,
    ).run()


if __name__ == "__main__":
    main()
