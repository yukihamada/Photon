#!/usr/bin/env python3
"""全学習データをマージするスクリプト"""

import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"

# マージ対象ファイル（重複削除済み＋新規ジャンル）
TARGET_FILES = [
    # === コア推論データ ===
    "logic_math.jsonl",          # 259件 - 論理・数学
    "reasoning.jsonl",           # 69件 - 推論
    "japan_knowledge.jsonl",     # 110件 - 日本知識
    "tool_calling.jsonl",        # 77件 - ツール呼び出し

    # === 日本語・文化 ===
    "japanese_cultural_logic.jsonl",  # 127件
    "japanese_expressions.jsonl",     # 56件
    "japanese_commonsense.jsonl",     # 10件

    # === 会話・ユーモア ===
    "witty_qa.jsonl",            # 30件
    "witty_companion.jsonl",     # 12件
    "hooking_greetings.jsonl",   # 15件
    "ai_comedy.jsonl",           # 10件
    "conversation_hooks.jsonl",  # 49件

    # === 時事・トレンド ===
    "current_events.jsonl",      # 13件
    "current_trends_2026.jsonl", # 10件
    "japan_news_2024_2025.jsonl",# 10件

    # === 実用・教養 ===
    "number_sense.jsonl",        # 12件
    "textbook_knowledge.jsonl",  # 12件
    "offline_mode.jsonl",        # 30件
    "top100_questions.jsonl",    # 99件

    # === ニッチジャンル ===
    "subculture.jsonl",          # 10件
    "dark_psychology.jsonl",     # 12件
    "creative_writing.jsonl",    # 12件
    "ultimate_lifehack.jsonl",   # 10件
    "thought_experiments.jsonl", # 10件

    # === その他 ===
    "identity_creator.jsonl",    # 16件
    "philosophy_mentor.jsonl",   # 7件
    "investment_career.jsonl",   # 10件
    "logic_to_emotion.jsonl",    # 10件
    "safety_deflection.jsonl",   # 10件
    "bias_neutralization.jsonl", # 10件
    "reasoning_40.jsonl",        # 39件
]

def load_jsonl(filepath):
    """JSONLファイルを読み込む"""
    items = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"  Warning: {filepath.name} - JSON parse error: {e}")
    return items

def get_user_message(item):
    """ユーザーメッセージを取得（重複判定用）"""
    messages = item.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""

def main():
    all_data = []
    seen_messages = set()
    stats = defaultdict(int)

    print("=" * 60)
    print("ElioChat 学習データマージ")
    print("=" * 60)

    for filename in TARGET_FILES:
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"✗ {filename} - ファイルなし")
            continue

        items = load_jsonl(filepath)
        added = 0

        for item in items:
            user_msg = get_user_message(item)
            if user_msg and user_msg not in seen_messages:
                seen_messages.add(user_msg)
                all_data.append(item)
                added += 1

        stats[filename] = added
        print(f"✓ {filename}: {added}件")

    # 保存
    output_path = DATA_DIR / "eliochat_v3_merged.jsonl"
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print("=" * 60)
    print(f"合計: {len(all_data)}件")
    print(f"出力: {output_path}")
    print("=" * 60)

    # カテゴリ別統計
    print("\n【カテゴリ別内訳】")
    categories = {
        "コア推論": ["logic_math.jsonl", "reasoning.jsonl", "japan_knowledge.jsonl", "tool_calling.jsonl"],
        "日本語・文化": ["japanese_cultural_logic.jsonl", "japanese_expressions.jsonl", "japanese_commonsense.jsonl"],
        "会話・ユーモア": ["witty_qa.jsonl", "witty_companion.jsonl", "hooking_greetings.jsonl", "ai_comedy.jsonl", "conversation_hooks.jsonl"],
        "時事・トレンド": ["current_events.jsonl", "current_trends_2026.jsonl", "japan_news_2024_2025.jsonl"],
        "実用・教養": ["number_sense.jsonl", "textbook_knowledge.jsonl", "offline_mode.jsonl", "top100_questions.jsonl"],
        "ニッチジャンル": ["subculture.jsonl", "dark_psychology.jsonl", "creative_writing.jsonl", "ultimate_lifehack.jsonl", "thought_experiments.jsonl"],
    }

    for cat_name, files in categories.items():
        total = sum(stats.get(f, 0) for f in files)
        print(f"  {cat_name}: {total}件")

if __name__ == "__main__":
    main()
