def user_permission(toolName: str, command: str):
    user_input = input(f"allow action : {toolName} : {command} [y/n] : ")
    if user_input.strip().lower() not in ["y", "yes"]:
        return False
    return True