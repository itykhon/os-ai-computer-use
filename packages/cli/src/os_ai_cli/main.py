import sys
import argparse
import logging

from os_ai_core.di import create_container
from os_ai_core.utils.logger import setup_logging
from os_ai_llm.types import ToolDescriptor
from os_ai_core.orchestrator import Orchestrator
from os_ai_llm_anthropic.config import MODEL_NAME, COMPUTER_TOOL_TYPE

import pyautogui


def main() -> int:
    parser = argparse.ArgumentParser(description="Universal Computer Use agent (CLI)")
    parser.add_argument("--task", type=str, required=False, help="Задача (на естественном языке)")
    parser.add_argument("--debug", action="store_true", help="Включить DEBUG логи")
    parser.add_argument("--provider", type=str, required=False, help="Провайдер LLM: anthropic|openai")
    args = parser.parse_args()

    logger = setup_logging(debug=args.debug)
    logger.info(f"Screen size detected: {pyautogui.size()[0]}x{pyautogui.size()[1]}; pause={pyautogui.PAUSE}, failsafe={pyautogui.FAILSAFE}")

    if args.task:
        task_text = args.task
    else:
        logger.info("Awaiting task input from stdin...")
        print("Введите задачу:")
        task_text = sys.stdin.readline().strip()

    inj = create_container(args.provider)
    from os_ai_llm.interfaces import LLMClient
    from os_ai_core.tools.registry import ToolRegistry
    client = inj.get(LLMClient)
    tools = inj.get(ToolRegistry)
    orch = Orchestrator(client, tools)

    # derive model display from screen (simple default). Main package has richer logic; keep basic here.
    screen_w, screen_h = pyautogui.size()
    tool_descs = [
        ToolDescriptor(
            name="computer",
            kind="computer_use",
            params={
                "type": COMPUTER_TOOL_TYPE,
                "display_width_px": screen_w,
                "display_height_px": screen_h,
            },
        )
    ]
    system_prompt = (
        "You are an expert desktop operator. Use the computer tool to complete the user's task. "
        "ONLY take a screenshot when needed. Prefer keyboard shortcuts. "
        "NEVER send empty key combos; always include a valid key or hotkey like 'cmd+space'. "
        "When using key/hold_key, provide 'key' or 'keys' as a non-empty string (e.g., 'cmd+space', 'ctrl+c'). "
        "For any action with coordinates, set coordinate_space='auto' in tool input."
    )

    try:
        msgs = orch.run(task_text, tool_descs, system_prompt, max_iterations=30)
    except KeyboardInterrupt:
        total_in = getattr(orch, 'total_input_tokens', 0)
        total_out = getattr(orch, 'total_output_tokens', 0)
        try:
            from os_ai_core.utils.costs import estimate_cost
            from os_ai_llm_anthropic.config import MODEL_NAME as _MODEL
            in_cost, out_cost, total_cost, _tier = estimate_cost(_MODEL, int(total_in), int(total_out))
            print(f"\nInterrupted by user (Ctrl+C)\n📈 Usage total in={total_in} out={total_out} cost=${total_cost:.6f} (input=${in_cost:.6f}, output=${out_cost:.6f})")
        except Exception:
            print("\nInterrupted by user (Ctrl+C)")
        return 130

    final_texts = []
    for m in msgs:
        if getattr(m, "role", None) == "assistant":
            for p in (getattr(m, "content", []) or []):
                try:
                    if getattr(p, "type", None) == "text":
                        final_texts.append(str(getattr(p, "text", "")))
                except Exception:
                    pass
    if final_texts:
        print("\n".join(final_texts).strip())

    # Print cumulative usage summary
    try:
        total_in = getattr(orch, 'total_input_tokens', 0)
        total_out = getattr(orch, 'total_output_tokens', 0)
        from os_ai_core.utils.costs import estimate_cost
        from os_ai_llm_anthropic.config import MODEL_NAME as _MODEL
        in_cost, out_cost, total_cost, _tier = estimate_cost(_MODEL, int(total_in), int(total_out))
        print(f"📈 Usage total in={total_in} out={total_out} cost=${total_cost:.6f} (input=${in_cost:.6f}, output=${out_cost:.6f})")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

