from pathlib import Path

def get_project_root() -> str:
    cwd = Path.cwd().resolve()
    return f"project root : {cwd}"