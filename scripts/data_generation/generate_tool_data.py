"""
Generate tool calling training data for iPhone AI app (ElioChat)
Template-based generation to ensure correct tool call format
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
import sys
sys.path.append(str(Path(__file__).parent))
from config import (
    ELIOCHAT_SYSTEM_PROMPT, OUTPUT_DIR, TOOL_DATA_PATH, DATA_CONFIG,
    TOOLS, TOOL_TRIGGERS
)


# Tool call templates with variations
TOOL_CALL_TEMPLATES = {
    "calendar.get_today_events": [
        {"user": "今日の予定を教えて", "think": "ユーザーが今日の予定を知りたいと言っている。\nカレンダー情報はリアルタイムで変化するため、私の知識だけでは正確に答えられない。\ncalendar.get_today_eventsツールを使用する必要がある。"},
        {"user": "今日のスケジュールは？", "think": "今日のスケジュールを確認する必要がある。\nカレンダーAPIを呼び出して最新の予定を取得する。"},
        {"user": "今日何か予定ある？", "think": "ユーザーが今日の予定を確認したい。\nカレンダーから予定を取得して回答する。"},
        {"user": "今日は何がある？", "think": "今日の予定を確認したいという質問。\nカレンダーツールで予定を取得する。"},
        {"user": "予定を確認して", "think": "予定の確認を求められている。\nカレンダーから今日のイベントを取得する。"},
    ],
    "calendar.create_event": [
        {"user": "明日の14時に会議を入れて", "think": "ユーザーが予定を作成したいと言っている。\n明日の14時に会議というイベントを作成する必要がある。", "args": {"title": "会議", "start_date": "明日14:00", "end_date": "明日15:00"}},
        {"user": "来週の月曜日にランチの予定を追加して", "think": "新しい予定の作成依頼。\n来週月曜日のランチイベントをカレンダーに追加する。", "args": {"title": "ランチ", "start_date": "来週月曜12:00", "end_date": "来週月曜13:00"}},
        {"user": "18時から飲み会の予定入れて", "think": "今日の18時からの飲み会を予定に追加する。", "args": {"title": "飲み会", "start_date": "今日18:00", "end_date": "今日20:00"}},
    ],
    "reminders.list_reminders": [
        {"user": "リマインダーを見せて", "think": "ユーザーがリマインダー一覧を確認したい。\nリマインダーAPIを呼び出して一覧を取得する。"},
        {"user": "やることリストは？", "think": "To-Doリストの確認依頼。\nリマインダーの一覧を取得する。"},
        {"user": "タスク一覧を教えて", "think": "タスク一覧を確認したいという要求。\nリマインダーから取得する。"},
    ],
    "reminders.create_reminder": [
        {"user": "牛乳を買うことをリマインドして", "think": "買い物のリマインダーを作成する依頼。\n「牛乳を買う」というリマインダーを作成する。", "args": {"title": "牛乳を買う"}},
        {"user": "明日までにレポート提出をリマインドして", "think": "期限付きのリマインダー作成依頼。\nレポート提出のリマインダーを明日期限で作成する。", "args": {"title": "レポート提出", "due_date": "明日"}},
        {"user": "薬を飲むことを覚えておいて", "think": "リマインダー作成の依頼。\n薬を飲むというタスクを作成する。", "args": {"title": "薬を飲む"}},
    ],
    "contacts.search_contacts": [
        {"user": "田中さんの電話番号を教えて", "think": "ユーザーが特定の人物の連絡先を知りたがっている。\n私は個人の連絡先情報を持っていない。\n連絡先を検索するツールを使う必要がある。", "args": {"query": "田中"}},
        {"user": "山田花子さんの連絡先は？", "think": "山田花子さんの連絡先を探す依頼。\n連絡先検索ツールを使用する。", "args": {"query": "山田花子"}},
        {"user": "お母さんの番号教えて", "think": "お母さんの電話番号を調べる依頼。\n連絡先から検索する。", "args": {"query": "お母さん"}},
    ],
    "photos.list_albums": [
        {"user": "写真アルバムを見せて", "think": "ユーザーが写真アルバムを確認したい。\nフォトライブラリからアルバム一覧を取得する。"},
        {"user": "アルバム一覧は？", "think": "アルバム一覧の確認依頼。\n写真アプリからアルバムを取得する。"},
    ],
    "photos.get_recent": [
        {"user": "最近の写真を見せて", "think": "最近撮影した写真を確認したいという要求。\n最近の写真を取得するツールを使用する。"},
        {"user": "この前撮った写真は？", "think": "最近の写真を確認したい。\nフォトライブラリから最近の写真を取得する。"},
    ],
    "ghost_search": [
        {"user": "最新のiPhone情報を検索して", "think": "最新のiPhone情報はリアルタイムで変化する。\n私の知識では最新情報を提供できない可能性がある。\nウェブ検索で最新情報を取得する。", "args": {"query": "iPhone 最新情報"}},
        {"user": "今日のニュースを教えて", "think": "ニュースは日々更新されるため、最新情報が必要。\n検索ツールで最新ニュースを取得する。", "args": {"query": "今日のニュース"}},
        {"user": "渋谷の美味しいラーメン屋を調べて", "think": "お店の情報は変動するため、検索で最新情報を取得する。", "args": {"query": "渋谷 ラーメン おすすめ"}},
        {"user": "明日の天気を詳しく知りたい", "think": "天気予報は気象データが必要。\n検索で詳細な天気予報を取得する。", "args": {"query": "明日の天気 詳細"}},
    ],
    "location.get_current_location": [
        {"user": "今どこにいる？", "think": "ユーザーの現在位置を確認する依頼。\n位置情報ツールを使用して現在地を取得する。"},
        {"user": "現在地を教えて", "think": "現在地の確認依頼。\nGPS情報から現在位置を取得する。"},
        {"user": "ここはどこ？", "think": "現在位置を知りたいという質問。\n位置情報を取得して回答する。"},
    ],
    "weather.get_current": [
        {"user": "今日の天気は？", "think": "天気情報はリアルタイムデータが必要。\n天気APIを呼び出して現在の天気を取得する。"},
        {"user": "傘いる？", "think": "傘が必要かどうかは天気次第。\n現在の天気情報を取得して判断材料を提供する。"},
        {"user": "今の気温を教えて", "think": "気温はリアルタイムで変化する。\n天気ツールで現在の気温を取得する。"},
        {"user": "大阪の天気は？", "think": "大阪の天気を確認したいという要求。\n天気ツールに場所を指定して取得する。", "args": {"location": "大阪"}},
    ],
    "notes.list_notes": [
        {"user": "メモを見せて", "think": "メモ一覧を確認したいという要求。\nメモアプリから一覧を取得する。"},
        {"user": "ノートの一覧は？", "think": "ノート一覧の確認依頼。\nメモツールで一覧を取得する。"},
    ],
    "notes.create_note": [
        {"user": "買い物リストをメモして。卵、牛乳、パン", "think": "買い物リストのメモ作成依頼。\n内容を整理してメモを作成する。", "args": {"title": "買い物リスト", "content": "卵、牛乳、パン"}},
        {"user": "アイデアをメモしておいて。新しいアプリの企画について", "think": "アイデアのメモを作成する依頼。\nメモツールで新規メモを作成する。", "args": {"title": "アイデア", "content": "新しいアプリの企画について"}},
    ],
}

# Additional variations for user inputs
USER_INPUT_VARIATIONS = {
    "calendar.get_today_events": [
        "今日って何か予定あったっけ？",
        "スケジュール確認お願い",
        "今日の予定チェック",
        "今日は暇？予定ある？",
        "今日のアポって何時だっけ",
    ],
    "reminders.list_reminders": [
        "やらなきゃいけないことある？",
        "To-Do確認して",
        "今日のタスクは？",
        "忘れてることない？",
    ],
    "contacts.search_contacts": [
        "鈴木部長の連絡先",
        "美容院の番号教えて",
        "佐藤さんにかけたいんだけど",
        "先生の電話番号は？",
    ],
    "weather.get_current": [
        "今日雨降る？",
        "外寒い？",
        "洗濯物干せる天気？",
        "東京の天気どう？",
        "今日は晴れ？",
    ],
    "ghost_search": [
        "それについて調べて",
        "詳しく検索して",
        "最新情報を探して",
        "もっと教えて、検索して",
        "ネットで調べてほしい",
    ],
}


def format_tool_call(tool_name: str, args: Dict = None) -> str:
    """Format a tool call in the correct format"""
    if args is None:
        args = {}
    tool_call = {"name": tool_name, "arguments": args}
    return f'<tool_call>\n{json.dumps(tool_call, ensure_ascii=False, indent=2)}\n</tool_call>'


def generate_tool_example(tool_name: str, template: Dict) -> Dict:
    """Generate a single tool calling example"""
    user_input = template["user"]
    thinking = template["think"]
    args = template.get("args", {})

    # Build the response
    tool_call = format_tool_call(tool_name, args)
    response = f"<think>\n{thinking}\n</think>\n\n{tool_call}"

    return {
        "messages": [
            {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ]
    }


def generate_variation_example(tool_name: str, user_input: str, base_template: Dict) -> Dict:
    """Generate an example with a user input variation"""
    thinking = base_template["think"]
    args = base_template.get("args", {})

    # Adjust args based on user input if needed
    if "args" in base_template and "query" in base_template["args"]:
        # Extract potential query from user input
        args = {"query": user_input.replace("教えて", "").replace("調べて", "").replace("検索して", "").strip()}

    tool_call = format_tool_call(tool_name, args)
    response = f"<think>\n{thinking}\n</think>\n\n{tool_call}"

    return {
        "messages": [
            {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ]
    }


def generate_multi_turn_example(tool_name: str) -> Dict:
    """Generate a multi-turn conversation example with tool usage"""
    # Simple multi-turn scenarios
    scenarios = [
        {
            "tool": "calendar.get_today_events",
            "conversation": [
                {"role": "user", "content": "今日の予定は？"},
                {"role": "assistant", "content": "<think>\n今日の予定を確認する依頼。\nカレンダーから予定を取得する。\n</think>\n\n<tool_call>\n{\"name\": \"calendar.get_today_events\", \"arguments\": {}}\n</tool_call>"},
                {"role": "user", "content": "<tool_response>\n[{\"title\": \"チームミーティング\", \"time\": \"14:00\"}]\n</tool_response>"},
                {"role": "assistant", "content": "<think>\nツールから予定情報を受け取った。\n14時にチームミーティングがある。\nユーザーにわかりやすく伝える。\n</think>\n\n今日は14時からチームミーティングがありますよ。"}
            ]
        },
        {
            "tool": "weather.get_current",
            "conversation": [
                {"role": "user", "content": "天気教えて"},
                {"role": "assistant", "content": "<think>\n天気を確認する依頼。\n天気APIで現在の天気を取得する。\n</think>\n\n<tool_call>\n{\"name\": \"weather.get_current\", \"arguments\": {}}\n</tool_call>"},
                {"role": "user", "content": "<tool_response>\n{\"condition\": \"晴れ\", \"temperature\": 22, \"humidity\": 45}\n</tool_response>"},
                {"role": "assistant", "content": "<think>\n天気情報を受け取った。\n晴れで気温22度、湿度45%。\n過ごしやすい天気だと伝える。\n</think>\n\n今日は晴れで気温は22度、湿度45%です。過ごしやすい天気ですね。"}
            ]
        },
        {
            "tool": "contacts.search_contacts",
            "conversation": [
                {"role": "user", "content": "佐藤さんの番号"},
                {"role": "assistant", "content": "<think>\n佐藤さんの連絡先を検索する依頼。\n連絡先ツールで検索する。\n</think>\n\n<tool_call>\n{\"name\": \"contacts.search_contacts\", \"arguments\": {\"query\": \"佐藤\"}}\n</tool_call>"},
                {"role": "user", "content": "<tool_response>\n[{\"name\": \"佐藤太郎\", \"phone\": \"090-1234-5678\"}]\n</tool_response>"},
                {"role": "assistant", "content": "<think>\n佐藤太郎さんの連絡先が見つかった。\n電話番号を伝える。\n</think>\n\n佐藤太郎さんの電話番号は090-1234-5678です。"}
            ]
        },
    ]

    # Find matching scenario
    for scenario in scenarios:
        if scenario["tool"] == tool_name:
            return {
                "messages": [
                    {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                    *scenario["conversation"]
                ]
            }

    # Return None if no matching scenario
    return None


def generate_tool_dataset(target_count: int = 6000) -> List[Dict]:
    """Generate the full tool calling dataset"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    examples = []

    # Calculate examples per tool
    tools = list(TOOL_CALL_TEMPLATES.keys())
    base_per_tool = target_count // len(tools)

    print(f"Generating {target_count} tool calling examples...")

    for tool_name in tqdm(tools, desc="Tool Data"):
        templates = TOOL_CALL_TEMPLATES[tool_name]

        # Generate from base templates
        for template in templates:
            examples.append(generate_tool_example(tool_name, template))

        # Generate variations
        if tool_name in USER_INPUT_VARIATIONS:
            base_template = templates[0]
            for variation in USER_INPUT_VARIATIONS[tool_name]:
                examples.append(generate_variation_example(tool_name, variation, base_template))

        # Generate multi-turn examples
        multi_turn = generate_multi_turn_example(tool_name)
        if multi_turn:
            for _ in range(base_per_tool // 10):  # 10% multi-turn
                examples.append(multi_turn)

        # Fill remaining with randomized base templates
        current_count = len([e for e in examples])
        needed = base_per_tool - (current_count // len(tools))
        for _ in range(max(0, needed)):
            template = random.choice(templates)
            examples.append(generate_tool_example(tool_name, template))

    # Shuffle and trim to target
    random.shuffle(examples)
    examples = examples[:target_count]

    # Save to file
    with open(TOOL_DATA_PATH, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"Generated {len(examples)} examples, saved to {TOOL_DATA_PATH}")
    return examples


if __name__ == "__main__":
    target = DATA_CONFIG["tool_calling"]["count"]
    generate_tool_dataset(target)
