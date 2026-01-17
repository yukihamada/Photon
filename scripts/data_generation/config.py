"""
Configuration for ElioChat-1.7B-Think-JP data generation
Uses OpenRouter API to access multiple teacher models
"""
import os

# OpenRouter API Configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Teacher Models
MODELS = {
    "deepseek_r1": "deepseek/deepseek-r1",
    "claude": "anthropic/claude-sonnet-4",
    "qwen_math": "qwen/qwen-2.5-72b-instruct",
}

# Data Distribution (30,000 total)
DATA_CONFIG = {
    "logic_math": {
        "count": 10500,
        "ratio": 0.35,
        "models": ["deepseek_r1", "qwen_math"],
        "description": "数学、コード、論理パズル、累乗計算"
    },
    "reasoning": {
        "count": 10500,
        "ratio": 0.35,
        "models": ["deepseek_r1", "claude"],
        "description": "フェルミ推定、議論、要約、分析"
    },
    "tool_calling": {
        "count": 6000,
        "ratio": 0.20,
        "models": ["template"],  # Template-based generation
        "description": "iPhoneアプリのツール呼び出し"
    },
    "anti_hallucination": {
        "count": 3000,
        "ratio": 0.10,
        "models": ["template"],  # Template-based generation
        "description": "「わかりません」と答えるケース"
    }
}

# System Prompt for ElioChat
ELIOCHAT_SYSTEM_PROMPT = """あなたはElioChat（エリオチャット）です。iPhoneで動作するプライバシー重視のローカルAIアシスタントです。

## 基本原則
1. 日本語で丁寧に、でも自然に会話します
2. 不確かな情報は推測せず、必要に応じてツールを使います
3. 思考過程を<think>タグで示してから回答します
4. 個人情報や最新情報が必要な場合は適切なツールを呼び出します

## 利用可能なツール
- calendar.get_today_events: 今日の予定を取得
- calendar.create_event: 予定を作成
- reminders.list_reminders: リマインダー一覧
- reminders.create_reminder: リマインダー作成
- contacts.search_contacts: 連絡先検索
- photos.list_albums: アルバム一覧
- photos.get_recent: 最近の写真
- ghost_search: ウェブ検索
- location.get_current_location: 現在地取得
- weather.get_current: 現在の天気
- notes.list_notes: メモ一覧
- notes.create_note: メモ作成

## 回答形式
1. まず<think>タグ内で思考過程を示す
2. その後、回答またはツール呼び出しを行う
3. ツール呼び出しは<tool_call>タグを使用"""

# Tool Definitions for iPhone AI App
TOOLS = {
    "calendar.get_today_events": {
        "description": "今日の予定を取得します",
        "arguments": {}
    },
    "calendar.create_event": {
        "description": "新しい予定を作成します",
        "arguments": {
            "title": "予定のタイトル",
            "start_date": "開始日時 (ISO8601)",
            "end_date": "終了日時 (ISO8601)",
            "notes": "メモ（オプション）"
        }
    },
    "reminders.list_reminders": {
        "description": "リマインダー一覧を取得します",
        "arguments": {}
    },
    "reminders.create_reminder": {
        "description": "リマインダーを作成します",
        "arguments": {
            "title": "リマインダーのタイトル",
            "due_date": "期限日時（オプション）",
            "notes": "メモ（オプション）"
        }
    },
    "contacts.search_contacts": {
        "description": "連絡先を検索します",
        "arguments": {
            "query": "検索クエリ（名前など）"
        }
    },
    "photos.list_albums": {
        "description": "写真アルバム一覧を取得します",
        "arguments": {}
    },
    "photos.get_recent": {
        "description": "最近の写真を取得します",
        "arguments": {
            "limit": "取得する枚数（デフォルト: 10）"
        }
    },
    "ghost_search": {
        "description": "ウェブ検索を実行します",
        "arguments": {
            "query": "検索クエリ"
        }
    },
    "location.get_current_location": {
        "description": "現在地を取得します",
        "arguments": {}
    },
    "weather.get_current": {
        "description": "現在の天気を取得します",
        "arguments": {
            "location": "場所（オプション、デフォルトは現在地）"
        }
    },
    "notes.list_notes": {
        "description": "メモ一覧を取得します",
        "arguments": {}
    },
    "notes.create_note": {
        "description": "新しいメモを作成します",
        "arguments": {
            "title": "メモのタイトル",
            "content": "メモの内容"
        }
    }
}

# Tool Trigger Keywords
TOOL_TRIGGERS = {
    "calendar.get_today_events": ["今日の予定", "スケジュール", "今日何がある", "予定を教えて", "今日は何"],
    "calendar.create_event": ["予定を入れて", "予定を作成", "イベント追加", "スケジュールに追加"],
    "reminders.list_reminders": ["リマインダー", "タスク一覧", "やること", "To-Do"],
    "reminders.create_reminder": ["リマインダー作成", "リマインドして", "思い出させて", "覚えておいて"],
    "contacts.search_contacts": ["連絡先", "電話番号", "メールアドレス", "の番号"],
    "photos.list_albums": ["アルバム", "写真フォルダ"],
    "photos.get_recent": ["最近の写真", "写真を見せて", "撮った写真"],
    "ghost_search": ["検索して", "調べて", "最新の", "ニュース", "について教えて"],
    "location.get_current_location": ["今どこ", "現在地", "ここはどこ"],
    "weather.get_current": ["天気", "気温", "雨降る", "傘いる"],
    "notes.list_notes": ["メモ一覧", "ノート", "メモを見せて"],
    "notes.create_note": ["メモして", "メモ作成", "書き留めて"]
}

# Output Paths
OUTPUT_DIR = "/Users/yuki/workspace/qwen-jp/data"
LOGIC_DATA_PATH = f"{OUTPUT_DIR}/logic_math.jsonl"
REASONING_DATA_PATH = f"{OUTPUT_DIR}/reasoning.jsonl"
TOOL_DATA_PATH = f"{OUTPUT_DIR}/tool_calling.jsonl"
ANTI_HALLUCINATION_DATA_PATH = f"{OUTPUT_DIR}/anti_hallucination.jsonl"
JAPAN_KNOWLEDGE_PATH = f"{OUTPUT_DIR}/japan_knowledge.jsonl"
CULTURAL_LOGIC_PATH = f"{OUTPUT_DIR}/japanese_cultural_logic.jsonl"
EXPRESSIONS_PATH = f"{OUTPUT_DIR}/japanese_expressions.jsonl"
MATH_TEMPLATES_PATH = f"{OUTPUT_DIR}/math_templates.jsonl"
FINAL_DATA_PATH = f"{OUTPUT_DIR}/eliochat_train_30k.jsonl"
