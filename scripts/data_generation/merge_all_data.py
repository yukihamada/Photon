"""
全データファイルをマージして学習用データセットを作成
"""
import json
import os
from collections import Counter

DATA_DIR = "/Users/yuki/workspace/qwen-jp/data"
OUTPUT_PATH = f"{DATA_DIR}/eliochat_final.jsonl"

# マージ対象のファイル（新規生成分のみ）
TARGET_FILES = [
    "logic_math.jsonl",
    "reasoning.jsonl",
    "tool_calling.jsonl",
    "japan_knowledge.jsonl",
    "japanese_cultural_logic.jsonl",
    "japanese_expressions.jsonl",
    "identity_creator.jsonl",
    "current_events.jsonl",
    "witty_qa.jsonl",
    "witty_companion.jsonl",
    "japanese_commonsense.jsonl",
    "bias_neutralization.jsonl",
    "philosophy_mentor.jsonl",
    "safety_deflection.jsonl",
    # バックグラウンドで生成中のものも含める（空でもOK）
    "offline_mode.jsonl",
    "conversation_hooks.jsonl",
    "reasoning_40.jsonl",
    "top100_questions.jsonl",
]

def load_jsonl(filepath):
    """JSONLファイルを読み込む"""
    items = []
    if not os.path.exists(filepath):
        return items
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return items

def validate_item(item):
    """データ形式を検証"""
    if "messages" not in item:
        return False
    messages = item["messages"]
    if not isinstance(messages, list) or len(messages) < 2:
        return False
    # system, user, assistant の順序確認
    roles = [m.get("role") for m in messages]
    if "user" not in roles or "assistant" not in roles:
        return False
    return True

def main():
    print("=" * 60)
    print("ElioChat学習データマージ")
    print("=" * 60)

    all_data = []
    category_counts = Counter()
    file_counts = {}

    for filename in TARGET_FILES:
        filepath = os.path.join(DATA_DIR, filename)
        items = load_jsonl(filepath)

        valid_items = [item for item in items if validate_item(item)]
        invalid_count = len(items) - len(valid_items)

        if invalid_count > 0:
            print(f"  警告: {filename} - {invalid_count}件の無効なデータをスキップ")

        file_counts[filename] = len(valid_items)
        all_data.extend(valid_items)

        # カテゴリ集計
        for item in valid_items:
            cat = item.get("metadata", {}).get("category", "unknown")
            category_counts[cat] += 1

    print("\n📁 ファイル別件数:")
    for filename, count in sorted(file_counts.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {filename}: {count}件")

    print(f"\n📊 カテゴリ別件数:")
    for cat, count in category_counts.most_common(20):
        print(f"  {cat}: {count}件")

    # 重複チェック（ユーザーメッセージベース）
    seen_queries = set()
    unique_data = []
    duplicate_count = 0

    for item in all_data:
        user_msg = ""
        for msg in item["messages"]:
            if msg["role"] == "user":
                user_msg = msg["content"][:200]  # 最初の200文字
                break

        if user_msg and user_msg not in seen_queries:
            seen_queries.add(user_msg)
            unique_data.append(item)
        else:
            duplicate_count += 1

    print(f"\n🔍 重複チェック:")
    print(f"  元データ: {len(all_data)}件")
    print(f"  重複: {duplicate_count}件")
    print(f"  ユニーク: {len(unique_data)}件")

    # 保存
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for item in unique_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n✅ 保存完了: {OUTPUT_PATH}")
    print(f"   総件数: {len(unique_data)}件")

    # 統計サマリー
    print("\n" + "=" * 60)
    print("📈 学習データ統計サマリー")
    print("=" * 60)
    print(f"総学習サンプル数: {len(unique_data)}件")

    # カテゴリ大分類
    major_categories = {
        "論理・数学": ["logic", "math", "calculation"],
        "推論・思考": ["reasoning", "fermi", "analysis"],
        "日本語・文化": ["japan", "cultural", "commonsense", "expression"],
        "ツール使用": ["tool"],
        "ウィット・ユーモア": ["witty", "companion", "philosophy"],
        "安全性・バイアス": ["safety", "bias", "deflection"],
        "その他": []
    }

    major_counts = Counter()
    for cat, count in category_counts.items():
        matched = False
        for major, keywords in major_categories.items():
            if any(kw in cat.lower() for kw in keywords):
                major_counts[major] += count
                matched = True
                break
        if not matched:
            major_counts["その他"] += count

    print("\n大分類:")
    for major, count in major_counts.most_common():
        pct = count / len(unique_data) * 100
        print(f"  {major}: {count}件 ({pct:.1f}%)")

if __name__ == "__main__":
    main()
