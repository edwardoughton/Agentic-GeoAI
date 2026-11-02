"""Optional Claude Agent SDK launcher. Run explicitly; uses paid API calls."""
import asyncio
import os
import sys
from pathlib import Path
from claude_agent_sdk import ClaudeAgentOptions, query

ROOT = Path(__file__).resolve().parents[1]

async def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY in this terminal before running.")
    if not (ROOT / "experiments/results.csv").exists():
        raise SystemExit("Run the revised notebook baseline first and save its results.")
    prompt = (
        "Carry out this optimization assignment in the current repository. "
        "The baseline has finished. Use this Python executable for experiments: "
        + sys.executable
        + ". Read the notebook source and saved run files; notebook kernel variables "
        "are not available to your process. Extract/reuse the runner or write a "
        "standalone experiment script without retraining the baseline or running "
        "all notebook cells. Never execute the final-test cell. "
        + (ROOT / "AGENT_HANDOFF.md").read_text(encoding="utf-8")
    )
    options = ClaudeAgentOptions(
        cwd=str(ROOT),
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        permission_mode="acceptEdits",
        max_turns=40,
        max_budget_usd=5.0,
    )
    async for message in query(prompt=prompt, options=options):
        print(message, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
