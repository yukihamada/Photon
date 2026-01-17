#!/usr/bin/env python3
"""
Compare responses from different Japanese LLMs with actual output
"""
import subprocess
import json
import time

# Models to compare
MODELS = [
    {
        "name": "Photon-1.7B",
        "path": "./outputs/Photon-1.7B-Instruct-v1-Q5_K_M.gguf",
        "size": "1.2GB",
        "params": "1.7B",
        "chat_format": "chatml",
    },
    {
        "name": "TinySwallow-1.5B",
        "path": "./outputs/comparison_models/TinySwallow-1.5B-Instruct-Q5_K_M.gguf",
        "size": "1.0GB",
        "params": "1.5B",
        "chat_format": "chatml",
    },
    {
        "name": "RakutenAI-7B",
        "path": "./outputs/comparison_models/RakutenAI-7B-instruct-q4_K_M.gguf",
        "size": "4.2GB",
        "params": "7B",
        "chat_format": "mistral",  # Rakuten uses Mistral format
    },
]

# Test prompts
TEST_PROMPTS = [
    {
        "id": "math",
        "prompt": "2の10乗はいくつですか？計算過程も教えてください。",
        "category": "数学",
    },
    {
        "id": "logic",
        "prompt": "AはBより背が高い。BはCより背が高い。一番背が高いのは誰？",
        "category": "論理",
    },
    {
        "id": "culture",
        "prompt": "「一期一会」の意味を簡潔に教えてください。",
        "category": "日本文化",
    },
    {
        "id": "creative",
        "prompt": "春をテーマに俳句を一つ詠んでください。",
        "category": "創作",
    },
]


def run_inference(model_path: str, prompt: str, chat_format: str, timeout: int = 90) -> tuple:
    """Run inference and return response with timing"""

    # Format prompt based on model
    if chat_format == "chatml":
        full_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    elif chat_format == "mistral":
        full_prompt = f"[INST] {prompt} [/INST]"
    else:
        full_prompt = f"User: {prompt}\nAssistant:"

    cmd = [
        "llama-cli",
        "-m", model_path,
        "-p", full_prompt,
        "-n", "300",
        "--temp", "0.7",
        "--no-display-prompt",
        "-c", "2048",
    ]

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start
        response = result.stdout.strip()
        # Clean up response
        response = response.replace("[end of text]", "").strip()
        return response, elapsed
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", timeout
    except Exception as e:
        return f"[ERROR: {e}]", 0


def main():
    print("=" * 80)
    print("日本語LLM 比較評価 - 実際の応答を確認")
    print("=" * 80)

    print("\n## 評価対象モデル\n")
    print("| モデル | パラメータ | サイズ | 開発元 |")
    print("|--------|-----------|--------|--------|")
    for m in MODELS:
        developer = "yukihamada" if "Photon" in m["name"] else "Sakana AI" if "Swallow" in m["name"] else "Rakuten"
        print(f"| {m['name']} | {m['params']} | {m['size']} | {developer} |")

    results = {}

    for test in TEST_PROMPTS:
        print(f"\n{'=' * 80}")
        print(f"## テスト: {test['category']} - {test['id']}")
        print(f"**質問**: {test['prompt']}")
        print("=" * 80)

        results[test["id"]] = {}

        for model in MODELS:
            print(f"\n### {model['name']} ({model['params']})")
            print("-" * 40)

            response, elapsed = run_inference(
                model["path"],
                test["prompt"],
                model["chat_format"]
            )

            results[test["id"]][model["name"]] = {
                "response": response,
                "time": elapsed,
            }

            # Check for thinking tags
            has_thinking = "<think>" in response and "</think>" in response
            thinking_status = "🧠 思考あり" if has_thinking else ""

            print(f"**応答時間**: {elapsed:.1f}秒 {thinking_status}")
            print(f"\n```")
            # Truncate very long responses
            if len(response) > 500:
                print(response[:500] + "...")
            else:
                print(response)
            print("```")

    # Summary
    print("\n" + "=" * 80)
    print("## 総合評価サマリー")
    print("=" * 80)

    print("\n| モデル | 平均応答時間 | 思考タグ | 特徴 |")
    print("|--------|-------------|----------|------|")

    for model in MODELS:
        total_time = 0
        thinking_count = 0
        for test_id, test_results in results.items():
            if model["name"] in test_results:
                total_time += test_results[model["name"]]["time"]
                if "<think>" in test_results[model["name"]]["response"]:
                    thinking_count += 1

        avg_time = total_time / len(TEST_PROMPTS)
        thinking_pct = thinking_count / len(TEST_PROMPTS) * 100

        if "Photon" in model["name"]:
            feature = "思考プロセス可視化"
        elif "Rakuten" in model["name"]:
            feature = "大規模・高精度"
        else:
            feature = "軽量・高速"

        print(f"| {model['name']} | {avg_time:.1f}秒 | {thinking_pct:.0f}% | {feature} |")

    # Save results
    with open("./outputs/comparison_responses.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n結果を ./outputs/comparison_responses.json に保存しました")


if __name__ == "__main__":
    main()
