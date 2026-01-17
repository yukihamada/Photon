"""
Data quality verification for ElioChat training data
Checks format, content quality, and consistency
"""
import json
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter
import re
import sys
sys.path.append(str(Path(__file__).parent))
from config import (
    OUTPUT_DIR, LOGIC_DATA_PATH, REASONING_DATA_PATH,
    TOOL_DATA_PATH, ANTI_HALLUCINATION_DATA_PATH
)


def load_jsonl(path: str) -> List[Dict]:
    """Load JSONL file"""
    examples = []
    if not Path(path).exists():
        return examples
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def check_message_format(example: Dict) -> Tuple[bool, str]:
    """Check if the message format is correct"""
    if "messages" not in example:
        return False, "Missing 'messages' key"

    messages = example["messages"]
    if not isinstance(messages, list) or len(messages) < 2:
        return False, "Messages should be a list with at least 2 items"

    # Check roles
    roles = [m.get("role") for m in messages]
    if roles[0] not in ["system", "user"]:
        return False, f"First message should be system or user, got {roles[0]}"

    # Check for assistant response
    if "assistant" not in roles:
        return False, "No assistant response found"

    # Check content
    for msg in messages:
        if "content" not in msg or not msg["content"]:
            return False, f"Empty content in {msg.get('role')} message"

    return True, "OK"


def check_thinking_format(response: str) -> Tuple[bool, str]:
    """Check if thinking tags are properly formatted"""
    has_think_open = "<think>" in response
    has_think_close = "</think>" in response

    if has_think_open and not has_think_close:
        return False, "Missing </think> closing tag"
    if has_think_close and not has_think_open:
        return False, "Missing <think> opening tag"

    # Check order
    if has_think_open and has_think_close:
        open_pos = response.index("<think>")
        close_pos = response.index("</think>")
        if open_pos > close_pos:
            return False, "<think> should come before </think>"

    return True, "OK"


def check_tool_call_format(response: str) -> Tuple[bool, str]:
    """Check if tool call format is correct"""
    has_tool_open = "<tool_call>" in response
    has_tool_close = "</tool_call>" in response

    if has_tool_open and not has_tool_close:
        return False, "Missing </tool_call> closing tag"
    if has_tool_close and not has_tool_open:
        return False, "Missing <tool_call> opening tag"

    if has_tool_open and has_tool_close:
        # Extract tool call content
        match = re.search(r'<tool_call>\s*(.*?)\s*</tool_call>', response, re.DOTALL)
        if match:
            tool_content = match.group(1)
            try:
                tool_json = json.loads(tool_content)
                if "name" not in tool_json:
                    return False, "Tool call missing 'name' field"
                if "arguments" not in tool_json:
                    return False, "Tool call missing 'arguments' field"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON in tool call: {e}"

    return True, "OK"


def check_japanese_content(text: str) -> bool:
    """Check if text contains Japanese characters"""
    # Japanese character ranges
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
    return bool(japanese_pattern.search(text))


def verify_dataset(path: str, name: str) -> Dict:
    """Verify a single dataset and return statistics"""
    print(f"\n{'='*60}")
    print(f"Verifying: {name}")
    print(f"Path: {path}")
    print(f"{'='*60}")

    examples = load_jsonl(path)

    if not examples:
        print(f"WARNING: No examples found!")
        return {"total": 0, "valid": 0, "errors": []}

    stats = {
        "total": len(examples),
        "valid": 0,
        "errors": [],
        "warnings": [],
        "has_thinking": 0,
        "has_tool_call": 0,
        "avg_response_length": 0,
    }

    total_response_length = 0

    for i, example in enumerate(examples):
        # Check format
        valid, msg = check_message_format(example)
        if not valid:
            stats["errors"].append(f"Example {i}: {msg}")
            continue

        # Get assistant response
        assistant_msg = None
        for m in example["messages"]:
            if m["role"] == "assistant":
                assistant_msg = m["content"]
                break

        if not assistant_msg:
            stats["errors"].append(f"Example {i}: No assistant message")
            continue

        total_response_length += len(assistant_msg)

        # Check thinking format
        valid, msg = check_thinking_format(assistant_msg)
        if not valid:
            stats["errors"].append(f"Example {i}: {msg}")
            continue

        if "<think>" in assistant_msg:
            stats["has_thinking"] += 1

        # Check tool call format
        valid, msg = check_tool_call_format(assistant_msg)
        if not valid:
            stats["errors"].append(f"Example {i}: {msg}")
            continue

        if "<tool_call>" in assistant_msg:
            stats["has_tool_call"] += 1

        # Check Japanese content
        if not check_japanese_content(assistant_msg):
            stats["warnings"].append(f"Example {i}: No Japanese in response")

        stats["valid"] += 1

    stats["avg_response_length"] = total_response_length / len(examples) if examples else 0

    # Print summary
    print(f"\nTotal examples: {stats['total']}")
    print(f"Valid examples: {stats['valid']} ({100*stats['valid']/stats['total']:.1f}%)")
    print(f"With thinking: {stats['has_thinking']} ({100*stats['has_thinking']/stats['total']:.1f}%)")
    print(f"With tool calls: {stats['has_tool_call']} ({100*stats['has_tool_call']/stats['total']:.1f}%)")
    print(f"Avg response length: {stats['avg_response_length']:.0f} chars")

    if stats["errors"][:5]:
        print(f"\nFirst 5 errors:")
        for err in stats["errors"][:5]:
            print(f"  - {err}")

    if stats["warnings"][:5]:
        print(f"\nFirst 5 warnings:")
        for warn in stats["warnings"][:5]:
            print(f"  - {warn}")

    return stats


def verify_all_datasets():
    """Verify all training datasets"""
    datasets = [
        (LOGIC_DATA_PATH, "Logic/Math"),
        (REASONING_DATA_PATH, "Reasoning"),
        (TOOL_DATA_PATH, "Tool Calling"),
        (ANTI_HALLUCINATION_DATA_PATH, "Anti-Hallucination"),
    ]

    all_stats = []
    for path, name in datasets:
        stats = verify_dataset(path, name)
        all_stats.append((name, stats))

    # Print overall summary
    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)

    total_examples = sum(s["total"] for _, s in all_stats)
    total_valid = sum(s["valid"] for _, s in all_stats)
    total_thinking = sum(s.get("has_thinking", 0) for _, s in all_stats)
    total_tool = sum(s.get("has_tool_call", 0) for _, s in all_stats)

    print(f"\nTotal examples: {total_examples}")
    if total_examples > 0:
        print(f"Total valid: {total_valid} ({100*total_valid/total_examples:.1f}%)")
        print(f"With thinking: {total_thinking} ({100*total_thinking/total_examples:.1f}%)")
        print(f"With tool calls: {total_tool} ({100*total_tool/total_examples:.1f}%)")

    print("\nBreakdown by category:")
    for name, stats in all_stats:
        print(f"  {name}: {stats['total']} examples ({stats['valid']} valid)")

    return all_stats


if __name__ == "__main__":
    verify_all_datasets()
