#!/usr/bin/env python3
"""
Evaluate Photon-1.7B against other LLMs
Tests: Japanese reasoning, tool calling, factual accuracy
"""
import subprocess
import json
import re
import time
from pathlib import Path

# Test cases
EVAL_CASES = [
    # Japanese Reasoning (数学・論理)
    {
        "id": "math_1",
        "category": "reasoning",
        "prompt": "2の10乗はいくつですか？",
        "expected_pattern": r"1024",
        "check_thinking": True,
    },
    {
        "id": "math_2",
        "category": "reasoning",
        "prompt": "1から10までの合計は？",
        "expected_pattern": r"55",
        "check_thinking": True,
    },
    {
        "id": "logic_1",
        "category": "reasoning",
        "prompt": "AはBより背が高い。BはCより背が高い。AとCはどちらが背が高い？",
        "expected_pattern": r"A",
        "check_thinking": True,
    },
    # Tool calling
    {
        "id": "tool_1",
        "category": "tool_call",
        "prompt": "今日の天気を教えて",
        "expected_pattern": r"<tool_call>|weather",
        "check_thinking": True,
    },
    {
        "id": "tool_2",
        "category": "tool_call",
        "prompt": "今日の予定を確認して",
        "expected_pattern": r"<tool_call>|calendar",
        "check_thinking": True,
    },
    # Hallucination prevention
    {
        "id": "halluc_1",
        "category": "hallucination",
        "prompt": "山田太郎さんの電話番号を教えて",
        "expected_pattern": r"<tool_call>|わかりません|できません|持っていません",
        "check_thinking": True,
    },
    # Japanese culture
    {
        "id": "culture_1",
        "category": "japanese",
        "prompt": "「一期一会」の意味を教えてください",
        "expected_pattern": r"一度|出会い|大切",
        "check_thinking": False,
    },
    # Creative
    {
        "id": "creative_1",
        "category": "creative",
        "prompt": "俳句を一つ詠んでください",
        "expected_pattern": r".{5,}",  # Just check it generates something
        "check_thinking": False,
    },
]

# Models to compare
MODELS = [
    {
        "name": "Photon-1.7B",
        "path": "./outputs/Photon-1.7B-Instruct-v1-Q5_K_M.gguf",
        "type": "gguf",
        "size_gb": 1.2,
        "chat_format": "chatml",  # <|im_start|>
    },
    {
        "name": "TinySwallow-1.5B",
        "path": "./outputs/comparison_models/TinySwallow-1.5B-Instruct-Q5_K_M.gguf",
        "type": "gguf",
        "size_gb": 1.0,
        "chat_format": "chatml",
    },
    {
        "name": "LFM2.5-1.2B-JP",
        "path": "./outputs/comparison_models/LFM2.5-1.2B-JP-Q5_K_M.gguf",
        "type": "gguf",
        "size_gb": 0.8,
        "chat_format": "plain",  # No special tokens
    },
]


def find_local_models():
    """Find local GGUF models for comparison"""
    models = []
    search_paths = [
        Path.home() / ".cache" / "lm-studio" / "models",
        Path.home() / "Library" / "Caches" / "llama.cpp",
        Path("/opt/homebrew/share/llama"),
        Path.home() / "models",
    ]

    for base_path in search_paths:
        if base_path.exists():
            for gguf in base_path.rglob("*.gguf"):
                # Skip our own models
                if "Photon" in str(gguf):
                    continue
                # Check size (skip very large models)
                if gguf.stat().st_size < 5 * 1024 * 1024 * 1024:  # < 5GB
                    models.append({
                        "name": gguf.stem,
                        "path": str(gguf),
                        "type": "gguf",
                    })
                    if len(models) >= 3:  # Limit to 3 comparison models
                        return models
    return models


def run_llama_cli(model_path: str, prompt: str, chat_format: str = "chatml", timeout: int = 60) -> str:
    """Run llama-cli with a prompt"""
    # Format based on chat format
    if chat_format == "chatml":
        full_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    else:
        full_prompt = f"User: {prompt}\nAssistant:"

    cmd = [
        "llama-cli",
        "-m", model_path,
        "-p", full_prompt,
        "-n", "256",
        "--temp", "0.7",
        "--no-display-prompt",
        "-c", "2048",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"


def evaluate_response(response: str, test_case: dict) -> dict:
    """Evaluate a single response"""
    result = {
        "passed": False,
        "has_thinking": False,
        "match_expected": False,
    }

    # Check for thinking tags
    if "<think>" in response and "</think>" in response:
        result["has_thinking"] = True

    # Check expected pattern
    if re.search(test_case["expected_pattern"], response, re.IGNORECASE):
        result["match_expected"] = True

    # Calculate pass
    if test_case["check_thinking"]:
        result["passed"] = result["has_thinking"] and result["match_expected"]
    else:
        result["passed"] = result["match_expected"]

    return result


def run_evaluation():
    """Run full evaluation"""
    print("=" * 70)
    print("Photon-1.7B vs Other Japanese LLMs Evaluation")
    print("=" * 70)

    # Use predefined models
    all_models = MODELS

    print(f"\nModels to evaluate: {len(all_models)}")
    for m in all_models:
        size = m.get("size_gb", "?")
        print(f"  - {m['name']} ({size} GB)")

    results = {}

    for model in all_models:
        print(f"\n{'=' * 70}")
        print(f"Evaluating: {model['name']}")
        print("=" * 70)

        model_results = {
            "total": 0,
            "passed": 0,
            "thinking": 0,
            "by_category": {},
            "details": [],
        }

        for test in EVAL_CASES:
            print(f"\n[{test['id']}] {test['prompt'][:40]}...")

            start = time.time()
            chat_format = model.get("chat_format", "chatml")
            response = run_llama_cli(model["path"], test["prompt"], chat_format)
            elapsed = time.time() - start

            eval_result = evaluate_response(response, test)

            # Update stats
            model_results["total"] += 1
            if eval_result["passed"]:
                model_results["passed"] += 1
            if eval_result["has_thinking"]:
                model_results["thinking"] += 1

            cat = test["category"]
            if cat not in model_results["by_category"]:
                model_results["by_category"][cat] = {"total": 0, "passed": 0}
            model_results["by_category"][cat]["total"] += 1
            if eval_result["passed"]:
                model_results["by_category"][cat]["passed"] += 1

            status = "✓" if eval_result["passed"] else "✗"
            think_status = "🧠" if eval_result["has_thinking"] else "  "
            print(f"  {status} {think_status} ({elapsed:.1f}s)")

            # Show snippet of response
            response_preview = response[:100].replace("\n", " ")
            print(f"  Response: {response_preview}...")

            model_results["details"].append({
                "id": test["id"],
                "passed": eval_result["passed"],
                "thinking": eval_result["has_thinking"],
                "time": elapsed,
            })

        results[model["name"]] = model_results

    # Print summary
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    print(f"\n{'Model':<25} {'Pass Rate':<12} {'Thinking':<12} {'Score':<10}")
    print("-" * 60)

    for name, res in results.items():
        pass_rate = res["passed"] / res["total"] * 100
        think_rate = res["thinking"] / res["total"] * 100
        score = (pass_rate + think_rate) / 2
        print(f"{name:<25} {pass_rate:>6.1f}%     {think_rate:>6.1f}%     {score:>6.1f}")

    print("\n" + "-" * 60)
    print("Category Breakdown (Photon-1.7B):")

    photon_results = results.get("Photon-1.7B-Q5", {})
    for cat, stats in photon_results.get("by_category", {}).items():
        rate = stats["passed"] / stats["total"] * 100
        print(f"  {cat:<15}: {stats['passed']}/{stats['total']} ({rate:.0f}%)")

    # Save results
    output_path = "./outputs/evaluation_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    run_evaluation()
