# restore files from trash bin, maintain their original relative paths  

# make sure that file is inside trash folder
# restore_file(path)
# 1. Build the path inside the trash.
# 2. Check it exists.
# 3. Compute its original relative path.
# 4. Construct the original destination.
# 5. Create parent directories if needed.
# 6. Move the file back.

from pathlib import Path
project_root = Path.cwd().resolve()

def restore_file(file_path: str) -> str:
    # Check for circular/malformed paths
    if not isinstance(file_path, str) or '..' in file_path:
        return "ERROR: Malformed path. Invalid input."
    try:
        file_path = Path(file_path)
        trash_root = project_root / "wasabi" / "trash"

        # create file path relative to trash bin if not already relative to trash 
        if not file_path.relative_to(trash_root):
            trash_path = project_root / "wasabi" / "trash" / file_path
        else:
            trash_path = file_path

        if not trash_path.exists():
            return f"ERROR : file not in trash can"
        
        original_relative_path = trash_path.relative_to(trash_root)

        destination = project_root / original_relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            return f"ERROR: Destination {destination} already exists."
        
        trash_path.rename(destination)
        return f"{file_path} moved from {trash_path} to {destination}"
    except PermissionError:
        return f"ERROR: Permission denied to move file to {destination}."
    except Exception as e:
        return f"ERROR : {str(e)}"

# Example Test for restore_file function
if __name__ == '__main__':
    print(restore_file("basic_loop.py"))
    print(restore_file("non_existent_file.py"))
    print(restore_file("..\basic_loop.py"))  # Check for malformed path

