"""
Shared wrapper around the Claude Code CLI (`claude -p`).

This is the single code path every part of DealSense AI uses to talk to
Claude — deal-field extraction (input/extractor.py) and risk scoring
(scoring/scorer.py) both call run_json_prompt() here. Using the CLI (backed
by the user's existing Claude subscription login) instead of the Anthropic
API means no separate API key is required.
"""
import json
import logging
import subprocess

import config

logger = logging.getLogger(__name__)


class ClaudeCLIError(Exception):
    """Raised when the `claude` CLI fails to run or returns no usable output."""


def run_prompt(prompt: str, timeout: int = None) -> str:
    """
    Send a prompt to Claude via the CLI and return the raw text response.

    Prompt is piped over stdin (never passed as a shell string) to avoid
    argument-length limits and shell injection.
    """
    timeout = timeout or config.CLAUDE_CLI_TIMEOUT

    try:
        result = subprocess.run(
            [config.CLAUDE_CLI_PATH, "-p"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise ClaudeCLIError(
            f"'{config.CLAUDE_CLI_PATH}' was not found on PATH. Install the "
            "Claude Code CLI (npm install -g @anthropic-ai/claude-code) and "
            "log in with your Claude subscription, or set CLAUDE_CLI_PATH "
            "in .env to the full path of the binary."
        )
    except subprocess.TimeoutExpired:
        raise ClaudeCLIError(f"Claude CLI timed out after {timeout}s")

    if result.returncode != 0:
        raise ClaudeCLIError(
            f"Claude CLI exited with code {result.returncode}: "
            f"{result.stderr.strip()}"
        )

    output = result.stdout.strip()
    if not output:
        raise ClaudeCLIError("Claude CLI returned empty output")

    return output


def extract_json(text: str) -> dict:
    """
    Pull a JSON object out of Claude's response, tolerating stray preamble
    or markdown code fences around the actual JSON.
    """
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError(f"No JSON object found in Claude output: {text[:200]!r}")

    candidate = text[start:end + 1]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Could not parse JSON from Claude output: {e}\n{candidate[:500]!r}"
        )


def run_json_prompt(prompt: str, timeout: int = None) -> dict:
    """Run a prompt through Claude and parse the response as JSON."""
    raw_text = run_prompt(prompt, timeout=timeout)
    return extract_json(raw_text)
