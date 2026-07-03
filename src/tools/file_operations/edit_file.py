import os 
# if file doesn't exists: agent creates new file, can create nested folders
# and write the new_text inside freshly created file 

# if file exists: we replace old_text with new_text in the specified path, file.

def edit_file(path: str, old_text: str, new_text: str) -> str:
    if os.path.exists(path) and old_text:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_text not in content:
            return f"text not found in file : {old_text}"
        
        content = content.replace(old_text, new_text)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"replaced '{old_text}' with '{new_text}' in {path}")
        return f"successfully edited {path}"
    
    else:
        # only create directory if path contains subdirectories
        dir_name = os.path.dirname(path)
        if dir_name: 
            os.makedirs(dir_name, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)

        print(f"created '{path}' added '{new_text}'")
        return f"successfully created path: {path}"
    
if __name__ == "__main__":
    edit_file(
        path="test.txt",
        old_text="goodbye world",
        new_text="hello world how are you",
    )

