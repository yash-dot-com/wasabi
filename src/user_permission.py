def user_permission(toolName: str, command: str):
    """
    Prompt the user for permission to perform an action.

    Args:
        toolName (str): The name of the tool requesting permission.
        command (str): The command that requires user permission.

    Returns:
        bool: True if permission is granted, False otherwise.
    """
    user_input = input(f"allow action : {toolName} : {command} [y/n] : ")
    if user_input.strip().lower() not in ["y", "yes"]:
        return False
    return True