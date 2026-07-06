# instead of given the agent capability to call command line tools 
# cmd helper will act as a scoped proxy
# such that agent can only perform a few controlled and scoped commands.

from pathlib import Path
import subprocess
from dataclasses import dataclass

@dataclass
class CommandResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int


PROJECT_ROOT = Path.cwd().resolve()
MAX_OUTPUT = 100_000

def run_command(args: list[str]) -> CommandResult:
    try:
        result = subprocess.run(
            ["git",*args],
            cwd=PROJECT_ROOT,
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

        return CommandResult(
            success=result.returncode == 0,
            stdout=stdout.strip(),
            stderr=stderr.strip(),
            exit_code=result.returncode,
        )

    except subprocess.TimeoutExpired:

        return CommandResult(
            success=False,
            stdout="",
            stderr="Git command timed out.",
            exit_code=-1,
        )

    except Exception as e:

        return CommandResult(
            success=False,
            stdout="",
            stderr=str(e),
            exit_code=-1,
        )