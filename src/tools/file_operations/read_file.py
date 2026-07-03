# actual python logic here 
# agent implementation will be just putting actual logic into a fn with try, except & error handling logic 

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return f"File contents of {path}: \n {content}"

# if you want to run/ test the logic from a file that also happens to be a importable module 
# then you can put the testing logic into if __name__ == __main__ block 
# when another file imports this module, python will read & load the functions and classes
# but it will skip everything inside this if block
if __name__ == "__main__":
    print(read_file("main.py"))
