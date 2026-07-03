import os
import sys
from rich import print
from pydantic import BaseModel
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from src.tools.security_tools.project_root_checker import check_project_root
from src.system_check import security_scan
import json

load_dotenv()

openai = os.getenv("OPENAI_API")
system_prompt_path = os.getenv("SYSTEM_PROMPT_PATH")

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
        print(f"Agent Initialized with {len(self.tools)} tools")

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
            )
        ]

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
    
    system_prompt = get_system_prompt(prompt_file_path)

    agent = Agent(api_key, system_prompt)

    while True:
        try:
            user_input = input("You : ")

            if user_input.strip().lower() in ["exit", "quit", "bye"]:
                print("EXITING")
                break

            if user_input.strip().lower() in ["scan", "security scan"]:
                scan_result = security_scan(project_root=project_root)
                if scan_result["safe"] == True:
                    print(f"[SUCCESS] : NO VULNERABILITIES FOUND\n")
                    print(json.dumps(scan_result, indent=2))
                else:
                    print(f"[FAILURE] : VULNERABILITIES FOUND\n")
                    print(json.dumps(scan_result, indent=2))
                    raise RuntimeError                    

            if not user_input.strip():
                continue

            assistant_reply = agent.chat(user_input)

            print(f"\nWasabi : {assistant_reply}\n")
            print("-"*90)

        except KeyboardInterrupt:
            print(f"\nEXITING\n")
            break
        except RuntimeError as e:
            print(f"\n[EXITING]\n")
            sys.exit(1)