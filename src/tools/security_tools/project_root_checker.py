# project root checker acts as a middleware to all CRUD tools
# it makes sure that if the agent tries to access any folder / files beyond this current project directory
# it will get an error string - access forbidden 

from pathlib import Path
project_root = Path.cwd().resolve()

# for testing if the agent edits example.py file outside the src folder specified as root
# project_root = "/Users/yash/Desktop/wasabi/src"

def check_project_root(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = project_root / p

    p = p.resolve()
    p.relative_to(project_root)

    return p

