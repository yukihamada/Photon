"""
Generate tool calling training data using API (DeepSeek-R1 / Claude)
Creates natural, diverse tool calling scenarios
"""
import json
import asyncio
import aiohttp
import ssl
import certifi
import random
from pathlib import Path
from typing import List, Dict
from tqdm.asyncio import tqdm
import sys
sys.path.append(str(Path(__file__).parent))
from config import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODELS,
    ELIOCHAT_SYSTEM_PROMPT, OUTPUT_DIR, TOOL_DATA_PATH, TOOLS
)

# SSL context for macOS
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# Tool scenarios for API generation
TOOL_SCENARIOS = [
    # Calendar
    {"tool": "calendar.get_today_events", "prompt": "今日の予定を確認したいという自然な日本語の質問を作って、それに対して<think>タグで思考過程を示し、calendar.get_today_eventsツールを呼び出す回答を生成してください。"},
    {"tool": "calendar.create_event", "prompt": "新しい予定を作成したいという自然な日本語の質問を作って（具体的な日時と内容を含めて）、それに対して<think>タグで思考過程を示し、calendar.create_eventツールを呼び出す回答を生成してください。"},

    # Reminders
    {"tool": "reminders.list_reminders", "prompt": "リマインダーやToDoリストを確認したいという自然な日本語の質問を作って、それに対して<think>タグで思考過程を示し、reminders.list_remindersツールを呼び出す回答を生成してください。"},
    {"tool": "reminders.create_reminder", "prompt": "何かをリマインドしてほしいという自然な日本語の依頼を作って（具体的なタスク内容を含めて）、それに対して<think>タグで思考過程を示し、reminders.create_reminderツールを呼び出す回答を生成してください。"},

    # Contacts
    {"tool": "contacts.search_contacts", "prompt": "誰かの連絡先（電話番号やメールアドレス）を知りたいという自然な日本語の質問を作って、それに対して<think>タグで思考過程を示し、contacts.search_contactsツールを呼び出す回答を生成してください。個人情報を推測で作らないという姿勢を示してください。"},

    # Weather
    {"tool": "weather.get_current", "prompt": "天気に関する自然な日本語の質問を作って（傘が必要か、今日の気温など）、それに対して<think>タグで思考過程を示し、weather.get_currentツールを呼び出す回答を生成してください。"},

    # Search
    {"tool": "ghost_search", "prompt": "最新情報や詳しい情報を調べてほしいという自然な日本語の質問を作って、それに対して<think>タグで思考過程を示し、ghost_searchツールを呼び出す回答を生成してください。"},

    # Location
    {"tool": "location.get_current_location", "prompt": "現在地を知りたいという自然な日本語の質問を作って、それに対して<think>タグで思考過程を示し、location.get_current_locationツールを呼び出す回答を生成してください。"},

    # Notes
    {"tool": "notes.create_note", "prompt": "何かをメモしておきたいという自然な日本語の依頼を作って（具体的な内容を含めて）、それに対して<think>タグで思考過程を示し、notes.create_noteツールを呼び出す回答を生成してください。"},

    # Photos
    {"tool": "photos.get_recent", "prompt": "最近撮った写真を見たいという自然な日本語の質問を作って、それに対して<think>タグで思考過程を示し、photos.get_recentツールを呼び出す回答を生成してください。"},
]

# Anti-hallucination scenarios (should use tool instead of making up info)
ANTI_HALLUCINATION_SCENARIOS = [
    "ユーザーが「山田太郎さんの電話番号教えて」と聞いています。AIは個人情報を推測で答えてはいけません。<think>タグで「私は個人の連絡先を知らない、ツールで検索する必要がある」という思考を示し、contacts.search_contactsツールを呼び出してください。",
    "ユーザーが「2025年の日本のGDPは？」と聞いています。AIは最新の統計を知らない可能性があります。<think>タグで「これは最新データが必要、検索すべき」という思考を示し、ghost_searchツールを呼び出してください。",
    "ユーザーが「今日東京で大きなイベントある？」と聞いています。AIはリアルタイム情報を持っていません。<think>タグで思考を示し、ghost_searchで検索してください。",
    "ユーザーが特定の飲食店の営業時間を聞いています。AIは店舗の最新情報を知りません。ツールで検索すべきです。",
]


async def call_openrouter(
    session: aiohttp.ClientSession,
    model: str,
    messages: List[Dict],
    semaphore: asyncio.Semaphore
) -> str:
    """Call OpenRouter API with rate limiting"""
    async with semaphore:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://eliochat.app",
            "X-Title": "ElioChat Training Data Generation"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 1500,
        }

        try:
            async with session.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    print(f"API Error {response.status}: {error_text[:200]}")
                    return None
        except Exception as e:
            print(f"Request error: {e}")
            return None


def parse_generated_content(raw: str, tool_name: str) -> Dict | None:
    """Parse the generated content into proper format"""
    if not raw:
        return None

    # Try to extract user question and assistant response
    lines = raw.strip().split('\n')

    user_content = None
    assistant_content = None

    # Look for patterns like "ユーザー:" or "質問:"
    current_role = None
    current_content = []

    for line in lines:
        lower = line.lower()
        if any(marker in line for marker in ["ユーザー:", "質問:", "User:", "Q:"]):
            if current_role == "assistant" and current_content:
                assistant_content = '\n'.join(current_content).strip()
            current_role = "user"
            # Extract content after the marker
            for marker in ["ユーザー:", "質問:", "User:", "Q:"]:
                if marker in line:
                    content = line.split(marker, 1)[1].strip()
                    current_content = [content] if content else []
                    break
        elif any(marker in line for marker in ["アシスタント:", "回答:", "Assistant:", "A:", "<think>"]):
            if current_role == "user" and current_content:
                user_content = '\n'.join(current_content).strip()
            current_role = "assistant"
            if "<think>" in line:
                current_content = [line]
            else:
                for marker in ["アシスタント:", "回答:", "Assistant:", "A:"]:
                    if marker in line:
                        content = line.split(marker, 1)[1].strip()
                        current_content = [content] if content else []
                        break
        elif current_role:
            current_content.append(line)

    # Get the last content
    if current_role == "user" and current_content:
        user_content = '\n'.join(current_content).strip()
    elif current_role == "assistant" and current_content:
        assistant_content = '\n'.join(current_content).strip()

    # If no clear structure, try to use the whole response
    if not user_content or not assistant_content:
        # Check if response contains tool_call
        if "<tool_call>" in raw and tool_name in raw:
            # Generate a simple question based on tool
            tool_questions = {
                "calendar.get_today_events": "今日の予定を教えて",
                "calendar.create_event": "明日の15時に会議を入れて",
                "reminders.list_reminders": "リマインダーを見せて",
                "reminders.create_reminder": "牛乳を買うことをリマインドして",
                "contacts.search_contacts": "田中さんの電話番号を教えて",
                "weather.get_current": "今日の天気は？",
                "ghost_search": "最新のiPhone情報を調べて",
                "location.get_current_location": "今どこにいる？",
                "notes.create_note": "買い物リストをメモして",
                "photos.get_recent": "最近の写真を見せて",
            }
            user_content = tool_questions.get(tool_name, "教えて")
            assistant_content = raw

    if not user_content or not assistant_content:
        return None

    # Validate that the response contains proper tags
    if "<think>" not in assistant_content:
        return None
    if "<tool_call>" not in assistant_content or tool_name not in assistant_content:
        return None

    return {
        "messages": [
            {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ]
    }


async def generate_tool_example(
    session: aiohttp.ClientSession,
    scenario: Dict,
    semaphore: asyncio.Semaphore
) -> Dict | None:
    """Generate a single tool calling example using API"""
    tool_name = scenario["tool"]
    prompt = scenario["prompt"]

    # Get tool info
    tool_info = TOOLS.get(tool_name, {})
    tool_desc = tool_info.get("description", "")
    tool_args = tool_info.get("arguments", {})

    system_prompt = f"""あなたは日本語AIアシスタント（ElioChat）の学習データを生成しています。
以下のツールを使用するシナリオを作成してください。

ツール名: {tool_name}
説明: {tool_desc}
引数: {json.dumps(tool_args, ensure_ascii=False)}

出力形式:
ユーザー: [自然な日本語の質問]
アシスタント: <think>
[思考過程を日本語で]
</think>

<tool_call>
{{"name": "{tool_name}", "arguments": {{...}}}}
</tool_call>

重要:
- ユーザーの質問は自然で多様なものにしてください
- <think>タグで思考過程を示してください
- <tool_call>タグでツールを呼び出してください
- 毎回異なる具体的な例を使ってください"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    model = MODELS["claude"] if random.random() > 0.5 else MODELS["deepseek_r1"]
    response = await call_openrouter(session, model, messages, semaphore)

    if response:
        return parse_generated_content(response, tool_name)
    return None


async def generate_tool_dataset_api(target_count: int = 200):
    """Generate tool calling dataset using API"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(10)
    examples = []

    connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []

        # Distribute scenarios
        for i in range(target_count):
            scenario = TOOL_SCENARIOS[i % len(TOOL_SCENARIOS)]
            tasks.append(generate_tool_example(session, scenario, semaphore))

        print(f"Generating {target_count} tool calling examples via API...")
        results = await tqdm.gather(*tasks, desc="Tool Data API")

        examples = [r for r in results if r is not None]

    # Save
    with open(TOOL_DATA_PATH, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"Generated {len(examples)} examples, saved to {TOOL_DATA_PATH}")
    return examples


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=200)
    args = parser.parse_args()
    asyncio.run(generate_tool_dataset_api(args.count))
