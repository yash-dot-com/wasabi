# instead of actually deleting the code, the file is moved to trash 
# architectural design 
# symlinks are not allowed 
# symlinks are pointer to other path, so we will not delete symlinks 
# unlink() deletes a file 
# recursive folder deletion is not yet implemented and allowed its dangerous 
# and we are not actually deleting the file, we are just moving it to trash for undo capibility

# parents=True creates any missing parent directories.
# exist_ok=True doesn't error if it already exists.

from pathlib import Path

project_root = Path("/Users/yash/Desktop/wasabi/")

def delete_file(file_path: str) -> str:
    try:
        file_path = Path(file_path)
        resolved = (project_root / file_path).resolve()

        if not resolved.exists():
            return f"ERROR : file doesn't exists"

        if not resolved.is_relative_to(project_root):
            return f"ERROR : file deletion outside the root working directory is forbidden"
        
        if resolved == project_root:
            return f"ERROR : deleting project root is forbidden"
        
        if resolved.is_dir():
            return f"ERROR : directory deletion is forbidden"
        
        if resolved.is_symlink():
            return f"ERROR : symlink detected, deletion is forbidden"
        
        # if all passed, we can move the file to trash instead of permanently deleting it 

        trash_path = (project_root/"./wasabi"/"trash")

        trash_path.mkdir(parents=True, exist_ok=True)

        # to maintain original structure of file we find relative path of file to root 
        relative_file_path = resolved.relative_to(project_root)

        destination_in_trash = trash_path/relative_file_path
        destination_in_trash.parent.mkdir(parents=True, exist_ok=True)

        resolved.rename(destination_in_trash)

        return f"file {resolved} moved to {destination_in_trash}"
    except PermissionError as e:
            return f"ERROR: Permission denied {str(e)}"

    except OSError as e:
            return f"ERROR: {str(e)}"

    except Exception as e:
            return f"ERROR: Unexpected error: {str(e)}"


if __name__ == "__main__":
    result = delete_file("example.py")
    print(result)

