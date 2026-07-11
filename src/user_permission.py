from collections.abc import Callable


def user_permission(
    tool_name: str,
    command: str,
    request_handler: Callable[[str, str], bool],
) -> bool:
    """
    Prompt the user for permission to perform an action.

    Args:
        tool_name (str): The name of the tool requesting permission.
        command (str): The command that requires user permission.
        request_handler: A host-provided function that obtains the decision.

    Returns:
        bool: True if permission is granted, False otherwise.
    """
    return bool(request_handler(tool_name, command))
