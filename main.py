import platform
import os
import sys
from rich import print
from dataclasses import dataclass, asdict
from pydantic import BaseModel
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import subprocess
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

def get_system_prompt(system_prompt_path: str):
    """ safely loads system instructions from specified file """
    if not system_prompt_path:
        print("SYSTEM PROMPT PATH MISSING")
        sys.exit(1)

    try:
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError as e:
        print(f"File not found : {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error Reading the system prompt file")
        sys.exit(1)
    
system_prompt = get_system_prompt(system_prompt_path)

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
    def __init__(self, api_key: str, system_prompt: str):
        self.client = OpenAI(api_key=api_key)
        # initialize messages array with system prompt for the agent.

        self.messages: List[Dict[str, Any]] = [
            {"role":"system", "content": system_prompt}
        ]
        self.tools: List[Tool] = []
        self._setup_tools()
        print(f"\nAgent Initialized with {len(self.tools)} tools")

    def _get_project_root(self) -> str:
        cwd = Path.cwd().resolve().as_posix()
        print(cwd)
        print(type(cwd))
        return cwd
        
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
                description="edit a file by replacing old_text with new_text. creates the file if it doesn't exist",
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
                name="get_project_root",
                description="get the path for current working directory",
                parameters={},
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

            # Tool(
            #     name="git_changed_files",
            #     description="get the statistics of what changed in the project, git diff --name-only underneath.",
            #     parameters={}
            # ),

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
    
    def _uv_project_dependency_tree(self):
        """
        returns the dependency tree for current working directory
        """
        subprocess_result = self._run_command("uv", ["tree"])
        return subprocess_result


    # 5 - create tools for the agent here
    def _read_file(self, path: str) -> str:
        path = check_project_root(path)

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"[TOOL RESPONSE]\n")
            return f"Contents of {path}: \n {content}"
        except FileNotFoundError as e:
            print(f"[TOOL EXECUTION FAILED]\n")
            return f"File not found: {path}"
        except Exception as e:
            print(f"[TOOL EXECUTION FAILED]\n")
            return f"Error reading file: {str(e)}"
        
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
            
            print(f"[TOOL RESPONSE] returning list of files")
            return f"contents of {path}:\n" + "\n".join(items)
        except Exception as e:
            # returning errors as string for LLM to understand and reason next step.
            print(f"[TOOL EXECUTION FAILED]\n")
            return f"Error listing the files: {str(e)}"
        
    def _delete_file(self, file_path: str) -> str:
        if user_permission("delete file", file_path) != True:
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
        path = check_project_root(path)

        try:
            if os.path.exists(path) and old_text:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                if old_text not in content:
                    return f"text not found in file {path}"
                
                content = content.replace(old_text, new_text)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"[EDITING] {path}\n")    
                print(f"[TOOL RESPONSE] replaced {old_text} with {new_text} in {path}")
                return f"successfully edited {path}"
            else:
                # create fresh file, possibly in nested path 
                dir_name = os.path.dirname(path)

                if dir_name: 
                    os.makedirs(dir_name, exist_ok=True)
                
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_text)

                print(f"[TOOL RESPONSE] added {new_text} in {path}")
                return f"successfully created path : {path}"
            
        except Exception as e:
            print(f"[TOOL EXECUTION FAILED]\n")
            return f"Error editing file: {str(e)}"

    def _execute_tools(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """ try-catch block for executing tools selected by the agent using conditions """
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "list_files":
                return self._list_files(tool_input.get("path", "."))
            elif tool_name == "edit_file":
                return self._edit_file(
                    tool_input["path"],
                    tool_input.get("old_text", ""),
                    tool_input["new_text"]
                )
            elif tool_name == "get_project_root":
                return self._get_project_root()
            elif tool_name == "delete_file":
                return self._delete_file(tool_input["file_path"])
            elif tool_name == "restore_file":
                return self._restore_file(tool_input["file_path"])
            elif tool_name == "git_status":
                return self._git_status()
            elif tool_name == "git_diff":
                return self._git_diff(tool_input["file_path"])
            # elif tool_name == "git_changed_file":
            #     return self._git_changed_file()
            elif tool_name == "git_log":
                return self._git_log(tool_input["limit"])
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

        self.messages.append({"role": "user", "content": user_input})

        # function to create array of tool description as per openai SDK requirement
        tools_schema = self.get_openai_tools_payload()

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

                # iterate over each requested tool call 
                for tool_call in tool_calls:
                    call_id = tool_call.id
                    tool_name = tool_call.function.name

                    # extract the tool call argument into dictionary
                    tool_input = json.loads(tool_call.function.arguments)

                    print(f"[TOOL CALL] : {tool_name} with arguments : {tool_input}")

                    execution_result = self._execute_tools(tool_name, tool_input)

                    # append the tool execution result to conversation memory 
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": tool_name,
                        "content": execution_result
                    })

                    # continue execution of further tools
                    continue 
            else:
                self.messages.append({"role":"assistant", "content":assistant_message.content})
                return assistant_message.content

  
if __name__ == "__main__":
    project_root = Path.cwd().resolve()
    api_key = os.environ.get("OPENAI_API")
    prompt_file_path = os.environ.get("SYSTEM_PROMPT_PATH")

    if not api_key or not prompt_file_path:
        print("Error: OPENAI_API not set")
        sys.exit(1)

    try:
        system_prompt = get_system_prompt(prompt_file_path)
        scan_result = security_scan(project_root=project_root)
        if scan_result["safe"] == True:
            print(f"[SUCCESS] : NO VULNERABILITIES FOUND\n")
            print(json.dumps(scan_result, indent=2))
        else:
            print(f"[FAILURE] : VULNERABILITIES FOUND\n")
            print(json.dumps(scan_result, indent=2))
            print(f"\n")
            raise RuntimeError 
    except RuntimeError as e:
        print(f"\n[EXITING]\n")
        sys.exit(1)

    agent = Agent(api_key, system_prompt)

    while True:
        try:
            user_input = input(f"\nYou : ")

            if user_input.strip().lower() in ["exit", "quit", "bye"]:
                print(f"EXITING\n")
                break                  

            if not user_input.strip():
                continue

            assistant_reply = agent.chat(user_input)

            print(f"\nWasabi : {assistant_reply}\n")
            print("-"*90)

        except KeyboardInterrupt:
            print(f"\nEXITING\n")
            break