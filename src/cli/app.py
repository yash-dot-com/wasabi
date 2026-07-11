"""Compact Rich CLI renderer for the Wasabi coding agent."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule


AgentFactory = Callable[[Callable[[dict[str, Any]], None], Callable[[str, str], bool]], Any]


class WasabiCLI:
    """Terminal rendering and input only; agent behavior remains outside this class."""

    def __init__(
        self,
        agent_factory: Optional[AgentFactory] = None,
        startup_error: Optional[str] = None,
        startup_status: Optional[str] = None,
    ) -> None:
        self.console = Console()
        self._agent_factory = agent_factory
        self._startup_error = startup_error
        self._startup_status = startup_status
        self._agent: Any = None

    def run(self) -> None:
        self._render_banner()
        if self._startup_error:
            self._render_error(self._startup_error)
            return

        try:
            if self._agent_factory is None:
                raise RuntimeError("No agent factory was provided.")
            self._agent = self._agent_factory(self._handle_event, self._request_permission)
        except Exception as error:
            self._render_error(str(error))
            return

        if self._startup_status:
            self.console.print(f"[dim]{self._startup_status}[/dim]\n")

        while True:
            try:
                user_input = self._read_user_input()
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[dim]Goodbye[/dim]")
                return

            if user_input.lower() in {"exit", "quit", "bye"}:
                self.console.print("[dim]Goodbye[/dim]")
                return
            if not user_input:
                continue

            self.console.print()
            self.console.print("[yellow]✽ Thinking…[/yellow]")
            try:
                response = self._agent.chat(user_input)
            except Exception as error:
                self._render_error(str(error))
                self._render_turn_divider()
                continue

            if response:
                self.console.print()
                self.console.print(Markdown(response))
            self._render_turn_divider()

    def _render_banner(self) -> None:
        self.console.print("[bold bright_green]●[/bold bright_green] [bold]Wasabi[/bold]\n")

    def _read_user_input(self) -> str:
        """Render a non-submitted placeholder hint above the terminal input line."""
        self.console.print("[dim]╭─ User[/dim]")
        return self.console.input("[bold white]╰─❯ [/bold white]").strip()

    def _render_turn_divider(self) -> None:
        """Keep each completed user/agent exchange visually separate."""
        self.console.print()
        self.console.print(Rule(style="dim #3b3b3b"))
        self.console.print()

    def _handle_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")
        if event_type == "tool_call":
            tool_name = event.get("tool_name", "tool")
            arguments = self._format_arguments(event.get("arguments", {}))
            suffix = f" [dim]{arguments}[/dim]" if arguments else ""
            self.console.print(f"[yellow] ✽ tool [/yellow] [bold]{tool_name}[/bold]{suffix}")
        elif event_type == "tool_result":
            tool_name = event.get("tool_name", "tool")
            duration = event.get("duration_seconds")
            duration_text = f" ({duration:.1f}s)" if isinstance(duration, (float, int)) else ""
            if event.get("status") == "failed":
                self.console.print(f"[red] ✽ failed [/red] [bold]{tool_name}[/bold][dim]{duration_text}[/dim]")
            else:
                self.console.print(f"[green] ✽ success [/green] [bold]{tool_name}[/bold][dim]{duration_text}[/dim]")
        elif event_type == "error":
            self._render_error(event.get("message", "An unexpected error occurred."))

    def _request_permission(self, tool_name: str, command: str) -> bool:
        detail = command or "No command details supplied"
        self.console.print()
        self.console.print(f"[yellow]●[/yellow] [bold]Permission required[/bold] [dim]· {tool_name}[/dim]")
        self.console.print(f"  [dim]⎸[/dim] {detail}")
        answer = self.console.input("[bold red]allow once? [y/N] [/bold red]")
        allowed = answer.strip().lower() in {"y", "yes"}
        marker = "[green] ✽ allowed[/green]" if allowed else "[red]✗ denied[/red]"
        self.console.print(marker)
        return allowed

    def _render_error(self, message: str) -> None:
        lines = str(message).splitlines() or ["An unexpected error occurred."]
        self.console.print(f"[red] ✽ Error: [/red] {lines[0]}")
        for line in lines[1:]:
            self.console.print(f"[dim] | [/dim] {line}")
        self.console.print(f"[red]  [/red]")

    @staticmethod
    def _format_arguments(arguments: Any) -> str:
        if not isinstance(arguments, dict):
            return json.dumps(arguments, ensure_ascii=False)
        return " ".join(
            f"{key}={json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value}"
            for key, value in arguments.items()
        )
