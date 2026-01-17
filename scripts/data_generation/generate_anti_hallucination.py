"""
Generate anti-hallucination training data
Teaches the model to:
1. Say "I don't know" when appropriate
2. Use tools instead of making up information
3. Acknowledge uncertainty
4. Avoid fabricating personal information, statistics, or facts
"""
import json
import random
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import sys
sys.path.append(str(Path(__file__).parent))
from config import (
    ELIOCHAT_SYSTEM_PROMPT, OUTPUT_DIR, ANTI_HALLUCINATION_DATA_PATH, DATA_CONFIG
)


# Templates for anti-hallucination examples
ANTI_HALLUCINATION_TEMPLATES = {
    # Personal information - should use contacts tool
    "personal_info_tool": [
        {
            "user": "田中太郎さんの電話番号は？",
            "thinking": "ユーザーが「田中太郎さん」の電話番号を聞いている。\n私は個人の連絡先情報を持っていない。\n勝手に番号を作り上げてはいけない。\n連絡先を検索するツールを使うべき。",
            "response": '<tool_call>\n{"name": "contacts.search_contacts", "arguments": {"query": "田中太郎"}}\n</tool_call>'
        },
        {
            "user": "山田さんの誕生日いつ？",
            "thinking": "山田さんの誕生日を聞かれている。\n私は個人の誕生日情報を持っていない。\n適当な日付を答えてはいけない。\n連絡先から情報を取得するか、不明と答えるべき。",
            "response": '<tool_call>\n{"name": "contacts.search_contacts", "arguments": {"query": "山田"}}\n</tool_call>'
        },
        {
            "user": "社長の住所教えて",
            "thinking": "社長の住所を聞かれている。\nこれは個人情報であり、私が知っている情報ではない。\n連絡先を検索するか、そのような情報は持っていないと答える。",
            "response": "社長の住所については、私の知識には含まれていません。連絡先から検索してみましょうか？\n\n<tool_call>\n{\"name\": \"contacts.search_contacts\", \"arguments\": {\"query\": \"社長\"}}\n</tool_call>"
        },
    ],
    # Statistics and data - should search or admit uncertainty
    "statistics_search": [
        {
            "user": "2024年の日本のGDPは？",
            "thinking": "ユーザーが2024年のGDPを聞いている。\nこれは変動する統計データであり、私の知識のカットオフ以降の情報かもしれない。\n正確な数値を推測で答えるべきではない。\n検索ツールで最新情報を取得すべき。",
            "response": '最新の統計データを検索します。\n\n<tool_call>\n{"name": "ghost_search", "arguments": {"query": "2024年 日本 GDP 最新"}}\n</tool_call>'
        },
        {
            "user": "今のドル円レートは？",
            "thinking": "為替レートはリアルタイムで変動する。\n私の知識は最新ではない可能性が高い。\n正確なレートを答えるには検索が必要。",
            "response": '為替レートは常に変動しますので、最新情報を検索します。\n\n<tool_call>\n{"name": "ghost_search", "arguments": {"query": "ドル円 レート 現在"}}\n</tool_call>'
        },
        {
            "user": "今日の東京の感染者数は？",
            "thinking": "感染者数は日々更新される情報。\nリアルタイムデータが必要。\n推測で数字を出すべきではない。",
            "response": '最新の感染者数を検索します。\n\n<tool_call>\n{"name": "ghost_search", "arguments": {"query": "東京 感染者数 今日"}}\n</tool_call>'
        },
    ],
    # Real-time information - should use tools
    "realtime_tool": [
        {
            "user": "今何時？",
            "thinking": "現在時刻はリアルタイム情報。\n私は正確な現在時刻を知らない。\n適当な時刻を答えてはいけない。",
            "response": "申し訳ありませんが、私は正確な現在時刻を把握していません。お使いのデバイスの時計をご確認ください。"
        },
        {
            "user": "今の株価教えて",
            "thinking": "株価はリアルタイムで変動する情報。\n私の知識では最新の株価は分からない。\n検索して最新情報を取得する必要がある。",
            "response": '株価は常に変動しますので、最新情報を検索します。\n\n<tool_call>\n{"name": "ghost_search", "arguments": {"query": "株価 日経平均 現在"}}\n</tool_call>'
        },
    ],
    # Factual questions with uncertainty
    "uncertain_facts": [
        {
            "user": "宇宙人は存在する？",
            "thinking": "宇宙人の存在は科学的に証明されていない。\n推測や断定的な回答は避けるべき。\n現時点での科学的見解を伝える。",
            "response": "宇宙人の存在については、現時点では科学的に証明されていません。宇宙の広大さから考えると、地球外生命体が存在する可能性はあると考える科学者も多いですが、確実な証拠は見つかっていません。"
        },
        {
            "user": "明日地震起きる？",
            "thinking": "地震の予測は現代の科学では不可能。\n適当な予測を答えてはいけない。\n科学的な事実を伝える。",
            "response": "残念ながら、地震の正確な予測は現代の科学技術では不可能です。日頃から防災対策を心がけることが大切です。"
        },
        {
            "user": "来年の経済どうなる？",
            "thinking": "将来の経済予測は不確実性が高い。\n断定的な予測は避けるべき。\n様々な見方があることを伝える。",
            "response": "経済の将来予測は非常に難しく、専門家の間でも意見が分かれます。最新の経済予測を確認しますか？\n\n<tool_call>\n{\"name\": \"ghost_search\", \"arguments\": {\"query\": \"日本経済 来年 予測\"}}\n</tool_call>"
        },
    ],
    # Made-up entities
    "fictional_entities": [
        {
            "user": "ゴルバトフ理論について教えて",
            "thinking": "「ゴルバトフ理論」という名前は聞いたことがない。\n存在しない可能性がある。\n知ったかぶりをせず、検索で確認するか不明と答える。",
            "response": "「ゴルバトフ理論」については、私の知識にはありません。もしかすると聞き間違いや、非常に専門的な理論かもしれません。検索してみましょうか？\n\n<tool_call>\n{\"name\": \"ghost_search\", \"arguments\": {\"query\": \"ゴルバトフ理論\"}}\n</tool_call>"
        },
        {
            "user": "マクドナルドの裏メニュー「ゴールデンバーガー」の値段は？",
            "thinking": "「ゴールデンバーガー」という裏メニューは聞いたことがない。\n存在しない可能性が高い。\n架空の値段を答えてはいけない。",
            "response": "「ゴールデンバーガー」という商品については、私の知識にはありません。マクドナルドの公式メニューか確認が必要です。検索してみますか？"
        },
    ],
    # Direct admission of not knowing
    "direct_unknown": [
        {
            "user": "あなたの本当の名前は？",
            "thinking": "私はAIアシスタント「ElioChat」であり、それが私の名前。\n「本当の名前」という概念は私には当てはまらない。",
            "response": "私はElioChatというAIアシスタントです。これが私の名前であり、それ以外の「本当の名前」はありません。"
        },
        {
            "user": "私の顔見える？",
            "thinking": "私はカメラにアクセスする機能を持っていない。\nユーザーの顔は見えない。\n正直に答える。",
            "response": "いいえ、私にはカメラへのアクセス機能がないため、あなたの顔を見ることはできません。"
        },
        {
            "user": "昨日私が食べた夕食は？",
            "thinking": "ユーザーが昨日何を食べたかは私には分からない。\nこの情報は私の知識にはない。\n推測で答えてはいけない。",
            "response": "申し訳ありませんが、あなたが昨日何を食べたかは私には分かりません。あなたが教えてくださらない限り、そのような個人的な情報は把握できません。"
        },
        {
            "user": "私の好きな色は？",
            "thinking": "ユーザーの好みの色は私には分からない。\n以前の会話で聞いていない限り、答えられない。\n推測で答えるのは不適切。",
            "response": "あなたの好きな色については、まだ伺っていませんので分かりません。よければ教えてください。"
        },
    ],
    # Calculations with verification mindset
    "calculation_verification": [
        {
            "user": "この会社の売上と利益から利益率を計算して。売上100億円、利益5億円。",
            "thinking": "利益率の計算は、利益÷売上×100で求められる。\n5億÷100億×100 = 5%\nただし、ユーザーが提供した数値に基づく計算であり、実際の会社の数値かどうかは確認できない。",
            "response": "提供いただいた数値で計算します。\n\n利益率 = 利益 ÷ 売上 × 100\n= 5億円 ÷ 100億円 × 100\n= 5%\n\n利益率は5%です。なお、これはお伝えいただいた数値に基づく計算結果です。"
        },
    ],
}


def generate_example(category: str, template: Dict) -> Dict:
    """Generate a single anti-hallucination example"""
    response_text = f"<think>\n{template['thinking']}\n</think>\n\n{template['response']}"

    return {
        "messages": [
            {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
            {"role": "user", "content": template["user"]},
            {"role": "assistant", "content": response_text}
        ]
    }


def generate_variations():
    """Generate additional variations of anti-hallucination examples"""
    variations = []

    # Personal info variations
    names = ["佐藤", "鈴木", "高橋", "渡辺", "伊藤", "中村", "小林", "加藤", "吉田", "山本"]
    info_types = [
        ("の電話番号は？", "電話番号"),
        ("の住所は？", "住所"),
        ("のメールアドレスは？", "メールアドレス"),
        ("の誕生日は？", "誕生日"),
    ]

    for name in names[:5]:
        for query_suffix, info_type in info_types:
            variations.append({
                "user": f"{name}さん{query_suffix}",
                "thinking": f"{name}さんの{info_type}を聞かれている。\n私は個人の{info_type}情報を持っていない。\n推測で答えてはいけない。\n連絡先を検索するツールを使う。",
                "response": f'<tool_call>\n{{"name": "contacts.search_contacts", "arguments": {{"query": "{name}"}}}}\n</tool_call>'
            })

    # Statistics variations
    years = ["2023年", "2024年", "2025年", "今年", "昨年"]
    stats = [
        ("の日本の人口は？", "日本 人口"),
        ("の出生率は？", "日本 出生率"),
        ("の失業率は？", "日本 失業率"),
        ("のインフレ率は？", "日本 インフレ率"),
    ]

    for year in years:
        for query_suffix, search_query in stats:
            variations.append({
                "user": f"{year}{query_suffix}",
                "thinking": f"{year}の統計データを聞かれている。\nこれは最新情報が必要。\n推測で数値を答えてはいけない。\n検索で確認する。",
                "response": f'最新の統計を検索します。\n\n<tool_call>\n{{"name": "ghost_search", "arguments": {{"query": "{year} {search_query}"}}}}\n</tool_call>'
            })

    return [generate_example("variation", v) for v in variations]


def generate_anti_hallucination_dataset(target_count: int = 3000) -> List[Dict]:
    """Generate the full anti-hallucination dataset"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    examples = []

    print(f"Generating {target_count} anti-hallucination examples...")

    # Generate from templates
    for category, templates in tqdm(ANTI_HALLUCINATION_TEMPLATES.items(), desc="Categories"):
        for template in templates:
            examples.append(generate_example(category, template))

    # Generate variations
    variations = generate_variations()
    examples.extend(variations)

    # Duplicate and vary to reach target count
    original_count = len(examples)
    while len(examples) < target_count:
        # Add slightly modified copies
        for ex in examples[:original_count]:
            if len(examples) >= target_count:
                break
            examples.append(ex)

    # Shuffle
    random.shuffle(examples)
    examples = examples[:target_count]

    # Save to file
    with open(ANTI_HALLUCINATION_DATA_PATH, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"Generated {len(examples)} examples, saved to {ANTI_HALLUCINATION_DATA_PATH}")
    return examples


if __name__ == "__main__":
    target = DATA_CONFIG["anti_hallucination"]["count"]
    generate_anti_hallucination_dataset(target)
