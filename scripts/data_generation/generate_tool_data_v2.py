"""
Generate diverse tool calling training data for iPhone AI app (ElioChat)
V2: Improved diversity - each question is unique
"""
import json
import random
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import sys
sys.path.append(str(Path(__file__).parent))
from config import ELIOCHAT_SYSTEM_PROMPT, OUTPUT_DIR, TOOL_DATA_PATH


# Diverse name lists for generating unique queries
JAPANESE_NAMES = [
    "田中", "山田", "佐藤", "鈴木", "高橋", "伊藤", "渡辺", "中村", "小林", "加藤",
    "吉田", "山口", "松本", "井上", "木村", "林", "斎藤", "清水", "山崎", "森",
    "池田", "橋本", "阿部", "石川", "山下", "中島", "石井", "小川", "前田", "岡田",
    "長谷川", "藤田", "後藤", "近藤", "村上", "遠藤", "青木", "坂本", "福田", "太田"
]

FIRST_NAMES = [
    "太郎", "花子", "一郎", "美咲", "健太", "愛", "翔太", "さくら", "大輔", "結衣",
    "拓也", "陽子", "直樹", "真由美", "浩二", "麻美", "誠", "友美", "学", "由美子"
]

RELATION_NAMES = [
    "お母さん", "お父さん", "おばあちゃん", "おじいちゃん", "姉", "兄", "妹", "弟",
    "叔父さん", "叔母さん", "いとこ", "彼氏", "彼女", "旦那", "妻", "上司", "部長",
    "先生", "友達", "親友", "同僚", "先輩", "後輩", "社長", "課長", "店長"
]

PLACES = [
    "東京", "大阪", "名古屋", "福岡", "札幌", "横浜", "神戸", "京都", "広島", "仙台",
    "渋谷", "新宿", "池袋", "銀座", "六本木", "表参道", "原宿", "品川", "上野", "浅草"
]

EVENT_TITLES = [
    "会議", "ミーティング", "打ち合わせ", "面接", "商談", "プレゼン", "報告会",
    "歓迎会", "送別会", "忘年会", "新年会", "飲み会", "ランチ", "ディナー", "デート",
    "病院", "歯医者", "美容院", "習い事", "ジム", "買い物", "映画", "コンサート",
    "友達と遊ぶ", "家族と食事", "親戚の集まり", "結婚式", "誕生日会", "同窓会"
]

REMINDER_TASKS = [
    "牛乳を買う", "卵を買う", "パンを買う", "野菜を買う", "肉を買う", "魚を買う",
    "薬を飲む", "薬局に行く", "病院の予約", "歯医者の予約", "美容院の予約",
    "電気代を払う", "ガス代を払う", "水道代を払う", "家賃を払う", "税金を払う",
    "レポートを提出", "書類を送る", "メールを返信", "電話をかける", "連絡する",
    "洗濯物を取り込む", "掃除をする", "ゴミを出す", "料理を作る", "買い物に行く",
    "本を返す", "図書館に行く", "銀行に行く", "郵便局に行く", "役所に行く"
]

SEARCH_TOPICS = [
    "最新のiPhone", "Androidスマホ おすすめ", "プログラミング 学習", "Python 入門",
    "美味しいラーメン屋", "おしゃれなカフェ", "コスパの良いレストラン", "デートスポット",
    "観光スポット", "温泉旅館", "ビジネスホテル", "格安航空券", "新幹線 時刻表",
    "映画 上映中", "人気のアニメ", "おすすめの本", "ゲーム 新作", "音楽 ランキング",
    "ダイエット 方法", "筋トレ メニュー", "ヨガ 効果", "健康 食事",
    "転職 サイト", "副業 おすすめ", "投資 始め方", "節約 コツ",
    "DIY 初心者", "料理 レシピ", "掃除 コツ", "収納 アイデア"
]

TIMES = ["9時", "10時", "11時", "12時", "13時", "14時", "15時", "16時", "17時", "18時", "19時", "20時"]
DAYS = ["今日", "明日", "明後日", "来週の月曜", "来週の火曜", "来週の水曜", "来週の木曜", "来週の金曜", "週末", "来月"]


def format_tool_call(tool_name: str, args: Dict = None) -> str:
    """Format a tool call in the correct format"""
    if args is None:
        args = {}
    tool_call = {"name": tool_name, "arguments": args}
    return f'<tool_call>\n{json.dumps(tool_call, ensure_ascii=False, indent=2)}\n</tool_call>'


def generate_calendar_get_examples(count: int) -> List[Dict]:
    """Generate calendar.get_today_events examples"""
    examples = []
    questions = [
        "今日の予定を教えて",
        "今日のスケジュールは？",
        "今日何か予定ある？",
        "今日は何がある？",
        "予定を確認して",
        "今日のアポ教えて",
        "今日って何か入ってる？",
        "スケジュール確認お願い",
        "今日の予定チェックして",
        "今日暇かな？予定ある？",
        "何時に何があるか教えて",
        "今日のタイムスケジュールは？",
        "カレンダー見せて",
        "今日のイベント教えて",
        "今日一日の流れを教えて",
    ]

    thinking_templates = [
        "ユーザーが今日の予定を確認したいと言っている。\nカレンダー情報はリアルタイムで変化するため、私の知識だけでは正確に答えられない。\ncalendar.get_today_eventsツールを使用する。",
        "今日のスケジュールを確認する必要がある。\nカレンダーAPIを呼び出して最新の予定を取得する。",
        "予定の確認依頼。\nカレンダーから今日のイベントを取得する。",
        "今日の予定を知りたいという要求。\nカレンダーツールで予定一覧を取得する。",
    ]

    used_questions = set()
    for _ in range(count):
        q = random.choice(questions)
        # Add slight variation if already used
        if q in used_questions and random.random() > 0.5:
            q = q.replace("教えて", "確認して").replace("は？", "どう？")
        used_questions.add(q)

        thinking = random.choice(thinking_templates)
        tool_call = format_tool_call("calendar.get_today_events", {})

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_calendar_create_examples(count: int) -> List[Dict]:
    """Generate calendar.create_event examples"""
    examples = []
    used = set()

    for _ in range(count):
        event = random.choice(EVENT_TITLES)
        time = random.choice(TIMES)
        day = random.choice(DAYS)

        key = f"{day}_{time}_{event}"
        attempt = 0
        while key in used and attempt < 10:
            event = random.choice(EVENT_TITLES)
            time = random.choice(TIMES)
            day = random.choice(DAYS)
            key = f"{day}_{time}_{event}"
            attempt += 1
        used.add(key)

        patterns = [
            f"{day}の{time}に{event}の予定を入れて",
            f"{day}{time}から{event}があるから予定追加して",
            f"{event}を{day}の{time}に入れて",
            f"{day}、{time}から{event}。予定作成して",
            f"{day}の{event}、{time}開始で登録して",
        ]
        question = random.choice(patterns)

        thinking = f"ユーザーが新しい予定を作成したいと言っている。\n{day}の{time}に「{event}」というイベントを作成する必要がある。\nカレンダー作成ツールを使用する。"

        tool_call = format_tool_call("calendar.create_event", {
            "title": event,
            "start_date": f"{day}{time}",
            "end_date": f"{day}{int(time[:-1])+1}時"
        })

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_contacts_examples(count: int) -> List[Dict]:
    """Generate contacts.search_contacts examples"""
    examples = []
    used = set()

    for _ in range(count):
        use_relation = random.random() > 0.6

        if use_relation:
            name = random.choice(RELATION_NAMES)
        else:
            surname = random.choice(JAPANESE_NAMES)
            if random.random() > 0.5:
                firstname = random.choice(FIRST_NAMES)
                name = f"{surname}{firstname}"
            else:
                name = f"{surname}さん"

        if name in used:
            continue
        used.add(name)

        patterns = [
            f"{name}の電話番号を教えて",
            f"{name}の連絡先は？",
            f"{name}に電話したいんだけど番号教えて",
            f"{name}のメールアドレス教えて",
            f"{name}の番号調べて",
            f"{name}に連絡取りたい",
        ]
        question = random.choice(patterns)

        thinking = f"ユーザーが「{name}」の連絡先を知りたがっている。\n私は個人の連絡先情報を持っていない。\n勝手に番号を作り上げてはいけない。\n連絡先を検索するツールを使う必要がある。"

        query_name = name.replace("さん", "")
        tool_call = format_tool_call("contacts.search_contacts", {"query": query_name})

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_reminders_list_examples(count: int) -> List[Dict]:
    """Generate reminders.list_reminders examples"""
    examples = []
    questions = [
        "リマインダーを見せて",
        "やることリストは？",
        "タスク一覧を教えて",
        "今日のタスクは何？",
        "やらなきゃいけないことある？",
        "To-Do確認して",
        "忘れてることない？",
        "リマインダー一覧",
        "今日やることリスト",
        "残ってるタスクある？",
    ]

    thinking_templates = [
        "ユーザーがリマインダー一覧を確認したい。\nリマインダーAPIを呼び出して一覧を取得する。",
        "To-Doリストの確認依頼。\nリマインダーの一覧を取得する。",
        "タスク一覧を確認したいという要求。\nリマインダーから取得する。",
    ]

    for _ in range(count):
        question = random.choice(questions)
        thinking = random.choice(thinking_templates)
        tool_call = format_tool_call("reminders.list_reminders", {})

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_reminders_create_examples(count: int) -> List[Dict]:
    """Generate reminders.create_reminder examples"""
    examples = []
    used = set()

    for _ in range(count):
        task = random.choice(REMINDER_TASKS)
        has_date = random.random() > 0.5
        day = random.choice(DAYS) if has_date else None

        key = f"{task}_{day}"
        if key in used:
            continue
        used.add(key)

        if has_date:
            patterns = [
                f"{day}までに{task}をリマインドして",
                f"{task}、{day}までね。覚えておいて",
                f"{day}に{task}するの忘れないようにして",
                f"リマインダー作成して。{task}、期限は{day}",
            ]
            args = {"title": task, "due_date": day}
        else:
            patterns = [
                f"{task}をリマインドして",
                f"{task}、忘れないように",
                f"覚えておいて、{task}",
                f"リマインダー追加して。{task}",
            ]
            args = {"title": task}

        question = random.choice(patterns)
        thinking = f"リマインダーを作成する依頼。\n「{task}」というタスクをリマインダーに追加する。"
        tool_call = format_tool_call("reminders.create_reminder", args)

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_weather_examples(count: int) -> List[Dict]:
    """Generate weather.get_current examples"""
    examples = []
    used = set()

    for _ in range(count):
        use_place = random.random() > 0.6
        place = random.choice(PLACES) if use_place else None

        key = place or "current"
        if key in used and random.random() > 0.3:
            continue
        used.add(key)

        if place:
            patterns = [
                f"{place}の天気は？",
                f"{place}は今日晴れる？",
                f"{place}の気温教えて",
                f"{place}って今日傘いる？",
            ]
            args = {"location": place}
        else:
            patterns = [
                "今日の天気は？",
                "傘いる？",
                "今の気温を教えて",
                "今日は晴れ？雨？",
                "外寒い？",
                "洗濯物干せる天気？",
                "天気予報教えて",
            ]
            args = {}

        question = random.choice(patterns)
        thinking = "天気情報はリアルタイムデータが必要。\n天気APIを呼び出して現在の天気を取得する。"
        tool_call = format_tool_call("weather.get_current", args)

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_search_examples(count: int) -> List[Dict]:
    """Generate ghost_search examples"""
    examples = []
    used = set()

    for _ in range(count):
        topic = random.choice(SEARCH_TOPICS)
        place = random.choice(PLACES) if "おすすめ" in topic or "スポット" in topic else None

        if place:
            query = f"{place} {topic}"
        else:
            query = topic

        if query in used:
            continue
        used.add(query)

        patterns = [
            f"{query}について調べて",
            f"{query}を検索して",
            f"{query}について教えて",
            f"{query}の最新情報は？",
            f"{query}って何がおすすめ？調べて",
        ]
        question = random.choice(patterns)

        thinking = f"「{query}」についての情報を求められている。\nこれは最新情報や詳細なデータが必要。\n私の知識だけでは不十分な可能性があるため、検索ツールを使用する。"
        tool_call = format_tool_call("ghost_search", {"query": query})

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_location_examples(count: int) -> List[Dict]:
    """Generate location.get_current_location examples"""
    examples = []
    questions = [
        "今どこにいる？",
        "現在地を教えて",
        "ここはどこ？",
        "自分の位置を確認して",
        "GPS情報教えて",
        "今いる場所は？",
        "位置情報を取得して",
    ]

    for _ in range(count):
        question = random.choice(questions)
        thinking = "ユーザーの現在位置を確認する依頼。\n位置情報ツールを使用して現在地を取得する。"
        tool_call = format_tool_call("location.get_current_location", {})

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_photos_examples(count: int) -> List[Dict]:
    """Generate photos examples"""
    examples = []

    # photos.list_albums
    album_questions = [
        "写真アルバムを見せて",
        "アルバム一覧は？",
        "フォトアルバム教えて",
        "写真フォルダを確認して",
    ]

    for q in album_questions:
        thinking = "ユーザーが写真アルバムを確認したい。\nフォトライブラリからアルバム一覧を取得する。"
        tool_call = format_tool_call("photos.list_albums", {})
        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    # photos.get_recent
    recent_questions = [
        "最近の写真を見せて",
        "この前撮った写真は？",
        "最近撮影した写真を表示して",
        "直近の写真を見たい",
    ]

    for q in recent_questions:
        thinking = "最近撮影した写真を確認したいという要求。\n最近の写真を取得するツールを使用する。"
        tool_call = format_tool_call("photos.get_recent", {})
        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_notes_examples(count: int) -> List[Dict]:
    """Generate notes examples"""
    examples = []

    # notes.list_notes
    list_questions = [
        "メモを見せて",
        "ノートの一覧は？",
        "メモ一覧表示して",
        "保存してあるメモを確認",
    ]

    for q in list_questions:
        thinking = "メモ一覧を確認したいという要求。\nメモアプリから一覧を取得する。"
        tool_call = format_tool_call("notes.list_notes", {})
        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    # notes.create_note
    note_contents = [
        ("買い物リスト", "卵、牛乳、パン、野菜"),
        ("アイデアメモ", "新しいアプリの企画について"),
        ("会議メモ", "次回のミーティングの議題"),
        ("旅行計画", "京都旅行の行きたい場所"),
        ("読書リスト", "読みたい本のリスト"),
        ("レシピメモ", "美味しかった料理のレシピ"),
        ("ワークアウト記録", "今日の運動メニュー"),
    ]

    for title, content in note_contents:
        patterns = [
            f"{title}をメモして。{content}",
            f"メモ作成。タイトルは{title}、内容は{content}",
            f"「{title}」でメモを作って。{content}について",
        ]
        question = random.choice(patterns)
        thinking = f"メモを作成する依頼。\nタイトル「{title}」、内容「{content}」のメモを作成する。"
        tool_call = format_tool_call("notes.create_note", {"title": title, "content": content})
        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{tool_call}"}
            ]
        })

    return examples


def generate_tool_dataset_v2(target_count: int = 500) -> List[Dict]:
    """Generate diverse tool calling dataset"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Distribution of tool types
    distribution = {
        "calendar_get": 0.10,
        "calendar_create": 0.15,
        "contacts": 0.20,
        "reminders_list": 0.08,
        "reminders_create": 0.12,
        "weather": 0.10,
        "search": 0.15,
        "location": 0.05,
        "photos": 0.02,
        "notes": 0.03,
    }

    examples = []

    print(f"Generating {target_count} diverse tool calling examples...")

    for tool_type, ratio in tqdm(distribution.items(), desc="Tool Types"):
        count = int(target_count * ratio)

        if tool_type == "calendar_get":
            examples.extend(generate_calendar_get_examples(count))
        elif tool_type == "calendar_create":
            examples.extend(generate_calendar_create_examples(count))
        elif tool_type == "contacts":
            examples.extend(generate_contacts_examples(count))
        elif tool_type == "reminders_list":
            examples.extend(generate_reminders_list_examples(count))
        elif tool_type == "reminders_create":
            examples.extend(generate_reminders_create_examples(count))
        elif tool_type == "weather":
            examples.extend(generate_weather_examples(count))
        elif tool_type == "search":
            examples.extend(generate_search_examples(count))
        elif tool_type == "location":
            examples.extend(generate_location_examples(count))
        elif tool_type == "photos":
            examples.extend(generate_photos_examples(count))
        elif tool_type == "notes":
            examples.extend(generate_notes_examples(count))

    # Shuffle
    random.shuffle(examples)

    # Save
    with open(TOOL_DATA_PATH, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"Generated {len(examples)} unique examples, saved to {TOOL_DATA_PATH}")
    return examples


if __name__ == "__main__":
    generate_tool_dataset_v2(500)
