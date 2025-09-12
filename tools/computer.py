from __future__ import annotations

from typing import Dict, Any, List


def computer_tool_handler(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Adapter from canonical ToolCall args to the legacy handler output.

    Returns Anthropic-style content blocks (list of dicts with type text/image).
    """
    action = args.get("action") or args.get("type")
    if not action:
        return [{"type": "text", "text": "error: missing 'action'"}]
    # Coordinate mapping: default to automatic model->screen transform like legacy path
    try:
        args.setdefault("coordinate_space", "auto")
    except Exception:
        pass
    # Lazy import to avoid circular import at module import time
    from main import handle_computer_action  # type: ignore
    return handle_computer_action(action, args)


