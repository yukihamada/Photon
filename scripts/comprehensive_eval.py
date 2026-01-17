#!/usr/bin/env python3
"""
Comprehensive evaluation of Japanese LLMs with varied questions
2025-2026 models comparison
"""
import subprocess
import json
import time
import re

# Models to compare (2025-2026 releases + base model)
MODELS = [
    {
        "name": "Photon-1.7B",
        "path": "./outputs/Photon-1.7B-Instruct-v1-Q5_K_M.gguf",
        "size": "1.2GB",
        "params": "1.7B",
        "developer": "yukihamada",
        "release": "2025/01",
        "chat_format": "chatml",
    },
    {
        "name": "Qwen3-1.7B",
        "path": "./outputs/comparison_models/Qwen3-1.7B-Q8_0.gguf",
        "size": "1.7GB",
        "params": "1.7B",
        "developer": "Alibaba",
        "release": "2025/04",
        "chat_format": "chatml",
    },
    {
        "name": "TinySwallow-1.5B",
        "path": "./outputs/comparison_models/TinySwallow-1.5B-Instruct-Q5_K_M.gguf",
        "size": "1.0GB",
        "params": "1.5B",
        "developer": "Sakana AI",
        "release": "2025",
        "chat_format": "chatml",
    },
    {
        "name": "Sarashina2.2-3B",
        "path": "./outputs/comparison_models/Sarashina2.2-3B-Q4_K_M.gguf",
        "size": "1.9GB",
        "params": "3B",
        "developer": "SB Intuitions",
        "release": "2024/12",
        "chat_format": "chatml",
    },
]

# Varied test questions
TEST_QUESTIONS = [
    # 数学・計算
    {"id": "math_1", "category": "数学", "q": "2の10乗を計算してください。", "answer_contains": ["1024"]},
    {"id": "math_2", "category": "数学", "q": "1+2+3+...+10の合計は？", "answer_contains": ["55"]},
    {"id": "math_3", "category": "数学", "q": "100を7で割った余りは？", "answer_contains": ["2"]},

    # 論理・推論
    {"id": "logic_1", "category": "論理", "q": "AはBより背が高い。BはCより背が高い。一番背が高いのは誰？", "answer_contains": ["A"]},
    {"id": "logic_2", "category": "論理", "q": "全ての犬は動物である。ポチは犬である。ポチは動物か？", "answer_contains": ["はい", "動物", "Yes"]},
    {"id": "logic_3", "category": "論理", "q": "りんごが3個、みかんが5個あります。果物は全部で何個？", "answer_contains": ["8"]},

    # 日本語・文化
    {"id": "jp_1", "category": "日本語", "q": "「一期一会」の意味を教えてください。", "answer_contains": ["一度", "出会い", "大切"]},
    {"id": "jp_2", "category": "日本語", "q": "「猫に小判」はどういう意味？", "answer_contains": ["価値", "わからない", "無駄"]},
    {"id": "jp_3", "category": "日本語", "q": "「さくら」を使った短い文を作ってください。", "answer_contains": []},

    # 知識・常識
    {"id": "know_1", "category": "知識", "q": "日本の首都はどこですか？", "answer_contains": ["東京"]},
    {"id": "know_2", "category": "知識", "q": "1年は何日ですか？", "answer_contains": ["365", "366"]},
    {"id": "know_3", "category": "知識", "q": "水の化学式は？", "answer_contains": ["H2O"]},

    # 創作
    {"id": "creative_1", "category": "創作", "q": "春をテーマに俳句を一つ詠んでください。", "answer_contains": []},
    {"id": "creative_2", "category": "創作", "q": "「希望」をテーマに一行詩を書いてください。", "answer_contains": []},

    # 説明・解説
    {"id": "explain_1", "category": "説明", "q": "なぜ空は青いのですか？簡潔に説明してください。", "answer_contains": ["光", "散乱"]},
    {"id": "explain_2", "category": "説明", "q": "AIとは何ですか？一文で説明してください。", "answer_contains": ["人工", "知能"]},

    # 実用
    {"id": "practical_1", "category": "実用", "q": "風邪を引いた時の対処法を3つ挙げてください。", "answer_contains": []},
    {"id": "practical_2", "category": "実用", "q": "おすすめの朝食メニューを教えてください。", "answer_contains": []},

    # エッジケース
    {"id": "edge_1", "category": "境界", "q": "私の誕生日はいつですか？", "answer_contains": ["わかりません", "知りません", "情報がありません", "存じません"]},
    {"id": "edge_2", "category": "境界", "q": "明日の天気を教えてください。", "answer_contains": ["わかりません", "予測できません", "情報がありません", "確認"]},
]


def run_inference(model_path: str, prompt: str, chat_format: str = "chatml", timeout: int = 90) -> tuple:
    """Run inference and return response with timing"""
    if chat_format == "chatml":
        full_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    else:
        full_prompt = f"User: {prompt}\nAssistant:"

    cmd = [
        "llama-cli",
        "-m", model_path,
        "-p", full_prompt,
        "-n", "200",
        "--temp", "0.7",
        "--no-display-prompt",
        "-c", "2048",
    ]

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - start
        response = result.stdout.strip().replace("[end of text]", "").strip()
        return response, elapsed
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", timeout
    except Exception as e:
        return f"[ERROR: {e}]", 0


def check_answer(response: str, expected: list) -> bool:
    """Check if response contains expected keywords"""
    if not expected:
        return len(response) > 10  # Just check it generated something
    return any(kw.lower() in response.lower() for kw in expected)


def has_thinking_tags(response: str) -> bool:
    """Check for <think> tags"""
    return "<think>" in response and "</think>" in response


def main():
    print("=" * 100)
    print("日本語LLM 総合評価 - 2025-2026年モデル比較")
    print("=" * 100)

    print("\n## 評価対象モデル\n")
    print(f"| {'モデル':<20} | {'パラメータ':<10} | {'サイズ':<8} | {'開発元':<15} | {'リリース':<10} |")
    print("|" + "-"*22 + "|" + "-"*12 + "|" + "-"*10 + "|" + "-"*17 + "|" + "-"*12 + "|")
    for m in MODELS:
        print(f"| {m['name']:<20} | {m['params']:<10} | {m['size']:<8} | {m['developer']:<15} | {m['release']:<10} |")

    results = {m["name"]: {"correct": 0, "thinking": 0, "total": 0, "time": 0, "responses": []} for m in MODELS}

    for q in TEST_QUESTIONS:
        print(f"\n{'='*100}")
        print(f"## [{q['id']}] {q['category']}: {q['q']}")
        print("=" * 100)

        for model in MODELS:
            response, elapsed = run_inference(model["path"], q["q"], model["chat_format"])

            correct = check_answer(response, q["answer_contains"])
            thinking = has_thinking_tags(response)

            results[model["name"]]["total"] += 1
            results[model["name"]]["time"] += elapsed
            if correct:
                results[model["name"]]["correct"] += 1
            if thinking:
                results[model["name"]]["thinking"] += 1

            results[model["name"]]["responses"].append({
                "id": q["id"],
                "response": response[:500],
                "correct": correct,
                "thinking": thinking,
                "time": elapsed,
            })

            # Display
            status = "✅" if correct else "❌"
            think_icon = "🧠" if thinking else "  "
            print(f"\n### {model['name']} {status} {think_icon} ({elapsed:.1f}s)")
            print("-" * 60)

            # Show response (truncated)
            display_response = response[:300].replace("\n", "\n> ")
            print(f"> {display_response}")
            if len(response) > 300:
                print("> ...")

    # Summary
    print("\n" + "=" * 100)
    print("## 総合評価サマリー")
    print("=" * 100)

    print(f"\n| {'モデル':<20} | {'正答率':<10} | {'思考タグ':<10} | {'平均時間':<10} | {'総合':<10} |")
    print("|" + "-"*22 + "|" + "-"*12 + "|" + "-"*12 + "|" + "-"*12 + "|" + "-"*12 + "|")

    for model in MODELS:
        r = results[model["name"]]
        acc = r["correct"] / r["total"] * 100
        think = r["thinking"] / r["total"] * 100
        avg_time = r["time"] / r["total"]
        score = (acc + think) / 2

        print(f"| {model['name']:<20} | {acc:>6.1f}%   | {think:>6.1f}%   | {avg_time:>6.1f}s   | {score:>6.1f}   |")

    # Category breakdown
    print("\n## カテゴリ別正答率 (Photon-1.7B)")
    print("-" * 60)

    categories = {}
    for q in TEST_QUESTIONS:
        cat = q["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "correct": 0}
        categories[cat]["total"] += 1

    for resp in results["Photon-1.7B"]["responses"]:
        q_data = next(q for q in TEST_QUESTIONS if q["id"] == resp["id"])
        if resp["correct"]:
            categories[q_data["category"]]["correct"] += 1

    for cat, stats in categories.items():
        rate = stats["correct"] / stats["total"] * 100
        bar = "█" * int(rate / 10) + "░" * (10 - int(rate / 10))
        print(f"  {cat:<10}: {bar} {stats['correct']}/{stats['total']} ({rate:.0f}%)")

    # Save results
    with open("./outputs/comprehensive_eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 100)
    print("結果を ./outputs/comprehensive_eval_results.json に保存しました")


if __name__ == "__main__":
    main()
