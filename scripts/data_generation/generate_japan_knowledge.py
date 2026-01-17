"""
Generate Japanese knowledge and culture training data
Focus on: Japanese history, geography, culture, society, business, traditions
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
    ELIOCHAT_SYSTEM_PROMPT, OUTPUT_DIR
)

# SSL context for macOS
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

JAPAN_KNOWLEDGE_PATH = f"{OUTPUT_DIR}/japan_knowledge.jsonl"

# Japanese History Questions
HISTORY_QUESTIONS = [
    "明治維新とは何ですか？その歴史的意義を説明してください。",
    "江戸時代の鎖国政策について教えてください。",
    "戦国時代の三英傑（織田信長、豊臣秀吉、徳川家康）について説明してください。",
    "平安時代の文化の特徴は何ですか？",
    "奈良時代の仏教文化について教えてください。",
    "第二次世界大戦後の日本の復興について説明してください。",
    "日本国憲法の三大原則を説明してください。",
    "縄文時代と弥生時代の違いは何ですか？",
    "遣唐使とは何でしたか？",
    "源平合戦について教えてください。",
    "関ヶ原の戦いの歴史的意義は？",
    "日露戦争の結果とその影響は？",
    "大正デモクラシーとは何ですか？",
    "高度経済成長期の日本について説明してください。",
    "バブル経済とその崩壊について教えてください。",
]

# Japanese Geography Questions
GEOGRAPHY_QUESTIONS = [
    "日本の47都道府県で最も面積が大きいのはどこですか？",
    "日本アルプスとは何ですか？",
    "富士山の高さと特徴を教えてください。",
    "日本の主要な平野を3つ挙げて説明してください。",
    "瀬戸内海の特徴は何ですか？",
    "北海道と本州の気候の違いを説明してください。",
    "日本の火山活動について教えてください。",
    "なぜ日本は地震が多いのですか？",
    "日本の四季の特徴を説明してください。",
    "琵琶湖について教えてください。",
    "日本の主要な河川を3つ挙げてください。",
    "沖縄の気候と文化の特徴は？",
    "東京湾の地理的特徴を説明してください。",
    "日本海側と太平洋側の気候の違いは？",
    "温泉大国日本の温泉の分布について教えてください。",
]

# Japanese Culture Questions
CULTURE_QUESTIONS = [
    "茶道の精神と作法について教えてください。",
    "華道（生け花）の歴史と流派について説明してください。",
    "能と歌舞伎の違いは何ですか？",
    "俳句の特徴と有名な俳人を教えてください。",
    "日本の伝統的な年中行事を5つ挙げて説明してください。",
    "着物の種類と着用シーンについて教えてください。",
    "日本庭園の特徴と様式について説明してください。",
    "お正月の伝統的な過ごし方を教えてください。",
    "七五三とは何ですか？",
    "お盆の意味と習慣について教えてください。",
    "武士道とは何ですか？",
    "日本の祭りの代表的なものを3つ教えてください。",
    "日本の伝統音楽（雅楽、三味線など）について説明してください。",
    "相撲の歴史と文化的意義を教えてください。",
    "日本の伝統工芸を3つ挙げて説明してください。",
]

# Japanese Food Questions
FOOD_QUESTIONS = [
    "和食がユネスコ無形文化遺産に登録された理由は？",
    "寿司の歴史と種類について教えてください。",
    "日本酒の製造方法と種類を説明してください。",
    "懐石料理と会席料理の違いは何ですか？",
    "日本の発酵食品を5つ挙げて説明してください。",
    "ラーメンの地域ごとの特徴を教えてください。",
    "おせち料理の意味と代表的な料理を教えてください。",
    "だしの種類と使い方について説明してください。",
    "日本の麺類（うどん、そば、素麺）の違いは？",
    "日本茶の種類と特徴を教えてください。",
    "和菓子の種類と季節感について説明してください。",
    "日本の郷土料理を3つ挙げて説明してください。",
    "味噌の種類と地域による違いを教えてください。",
    "日本の食事マナーについて教えてください。",
    "精進料理とは何ですか？",
]

# Japanese Society Questions
SOCIETY_QUESTIONS = [
    "日本の教育制度について説明してください。",
    "日本の医療保険制度について教えてください。",
    "日本の年金制度の仕組みを説明してください。",
    "日本の雇用慣行（終身雇用、年功序列）について教えてください。",
    "日本の少子高齢化の現状と課題は？",
    "日本の選挙制度について説明してください。",
    "日本の司法制度の特徴は何ですか？",
    "日本の地方自治について教えてください。",
    "日本の祝日を5つ挙げて、その由来を説明してください。",
    "日本の防災対策について説明してください。",
    "日本の交通システムの特徴は？",
    "日本のコンビニ文化について教えてください。",
    "日本の住宅事情について説明してください。",
    "日本の労働環境の課題は何ですか？",
    "日本の環境政策について教えてください。",
]

# Japanese Business Questions
BUSINESS_QUESTIONS = [
    "日本企業の特徴的な経営スタイルを説明してください。",
    "日本の名刺交換のマナーについて教えてください。",
    "日本の株式市場（東京証券取引所）について説明してください。",
    "日本の主要産業を5つ挙げて説明してください。",
    "日本のものづくりの強みは何ですか？",
    "日本企業の意思決定プロセス（稟議制度など）について教えてください。",
    "日本の中小企業の役割と課題は？",
    "日本の農業の現状と課題を説明してください。",
    "日本の観光産業について教えてください。",
    "日本のスタートアップ環境について説明してください。",
    "日本の貿易の特徴は？",
    "日本の技術力が世界で評価される分野は？",
    "日本のサービス業の特徴（おもてなし）について教えてください。",
    "日本の金融システムについて説明してください。",
    "日本企業のCSR活動について教えてください。",
]

# Japanese Language Questions
LANGUAGE_QUESTIONS = [
    "日本語の三種類の文字（ひらがな、カタカナ、漢字）の役割を説明してください。",
    "敬語の種類と使い分けについて教えてください。",
    "日本語の方言について説明してください。",
    "日本語の特徴的な文法構造は何ですか？",
    "外来語が日本語に与えた影響は？",
    "日本語の「空気を読む」という表現の意味と文化的背景は？",
    "日本語のオノマトペの特徴を教えてください。",
    "敬語を使う場面と注意点を説明してください。",
    "日本語の「間」の概念について教えてください。",
    "日本語学習で難しいとされる点は何ですか？",
]

# Modern Japan Questions
MODERN_JAPAN_QUESTIONS = [
    "日本のポップカルチャー（アニメ、漫画）の世界的影響は？",
    "日本のゲーム産業の歴史と現状を教えてください。",
    "日本のロボット技術について説明してください。",
    "日本の新幹線の技術的特徴は？",
    "日本のエネルギー政策の現状と課題は？",
    "日本のデジタル化の現状について教えてください。",
    "日本の宇宙開発について説明してください。",
    "日本のAI研究の現状は？",
    "日本の再生可能エネルギーへの取り組みは？",
    "日本のサイバーセキュリティ対策について教えてください。",
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
            "temperature": 0.7,
            "max_tokens": 2048,
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


def format_response_with_thinking(question: str, raw_response: str) -> str:
    """Format response with proper <think> tags"""
    if "<think>" in raw_response and "</think>" in raw_response:
        return raw_response

    # Generate thinking based on question type
    thinking_parts = []

    if any(word in question for word in ["歴史", "時代", "戦争", "維新", "幕府"]):
        thinking_parts.append("歴史的な質問なので、時系列と因果関係を整理する")
        thinking_parts.append("重要な出来事と人物を特定する")
        thinking_parts.append("歴史的意義を説明する")
    elif any(word in question for word in ["地理", "県", "山", "川", "海", "気候"]):
        thinking_parts.append("地理的な情報を整理する")
        thinking_parts.append("特徴や数値データを確認する")
        thinking_parts.append("他の地域との比較を含める")
    elif any(word in question for word in ["文化", "伝統", "茶道", "着物", "祭り"]):
        thinking_parts.append("日本文化の背景を理解する")
        thinking_parts.append("歴史的な発展と現代での意義を説明する")
        thinking_parts.append("具体例を挙げる")
    elif any(word in question for word in ["料理", "食", "酒", "和食"]):
        thinking_parts.append("日本の食文化の特徴を整理する")
        thinking_parts.append("地域や季節との関連を説明する")
        thinking_parts.append("具体的な例を挙げる")
    elif any(word in question for word in ["社会", "制度", "教育", "医療", "年金"]):
        thinking_parts.append("日本の社会システムの特徴を整理する")
        thinking_parts.append("歴史的背景と現状を説明する")
        thinking_parts.append("課題や今後の展望にも触れる")
    elif any(word in question for word in ["企業", "ビジネス", "経営", "産業"]):
        thinking_parts.append("日本のビジネス慣行の特徴を整理する")
        thinking_parts.append("国際比較の視点を含める")
        thinking_parts.append("具体例を挙げる")
    elif any(word in question for word in ["日本語", "言葉", "敬語", "文字"]):
        thinking_parts.append("日本語の言語学的特徴を整理する")
        thinking_parts.append("文化的背景との関連を説明する")
        thinking_parts.append("具体例を挙げる")
    else:
        thinking_parts.append("質問の内容を正確に理解する")
        thinking_parts.append("関連する知識を整理する")
        thinking_parts.append("論理的に説明する")

    thinking = "\n".join(thinking_parts)
    return f"<think>\n{thinking}\n</think>\n\n{raw_response}"


async def generate_single_example(
    session: aiohttp.ClientSession,
    question: str,
    category: str,
    model_key: str,
    semaphore: asyncio.Semaphore
) -> Dict | None:
    """Generate a single training example"""
    messages = [
        {
            "role": "system",
            "content": """あなたは日本の文化・歴史・社会に詳しい専門家です。
質問に対して、正確で詳しい回答を日本語で提供してください。
- 具体的な事実やデータを含めてください
- 歴史的背景や文化的意義も説明してください
- わかりやすく構造化された回答をしてください
思考過程を示してから回答してください。"""
        },
        {
            "role": "user",
            "content": question
        }
    ]

    model = MODELS.get(model_key, MODELS["claude"])
    response = await call_openrouter(session, model, messages, semaphore)

    if response:
        formatted_response = format_response_with_thinking(question, response)
        return {
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": formatted_response}
            ],
            "_category": category
        }
    return None


async def generate_japan_knowledge_dataset(target_count: int = 3000):
    """Generate the full Japanese knowledge dataset"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # All question categories
    all_questions = {
        "history": HISTORY_QUESTIONS,
        "geography": GEOGRAPHY_QUESTIONS,
        "culture": CULTURE_QUESTIONS,
        "food": FOOD_QUESTIONS,
        "society": SOCIETY_QUESTIONS,
        "business": BUSINESS_QUESTIONS,
        "language": LANGUAGE_QUESTIONS,
        "modern": MODERN_JAPAN_QUESTIONS,
    }

    # Rate limiting: 10 concurrent requests
    semaphore = asyncio.Semaphore(10)

    examples = []

    connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []

        # Distribute questions across categories
        categories = list(all_questions.keys())
        questions_per_category = target_count // len(categories)

        for category, questions in all_questions.items():
            for i in range(questions_per_category):
                question = questions[i % len(questions)]
                # Alternate between models
                model_key = "claude" if i % 2 == 0 else "deepseek_r1"
                tasks.append(generate_single_example(
                    session, question, category, model_key, semaphore
                ))

        # Execute with progress bar
        print(f"Generating {len(tasks)} Japanese knowledge examples...")
        results = await tqdm.gather(*tasks, desc="Japan Knowledge")

        # Filter out None results
        examples = [r for r in results if r is not None]

    # Remove category tag before saving
    for example in examples:
        if "_category" in example:
            del example["_category"]

    # Save to file
    with open(JAPAN_KNOWLEDGE_PATH, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"Generated {len(examples)} examples, saved to {JAPAN_KNOWLEDGE_PATH}")
    return examples


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=3000)
    args = parser.parse_args()
    asyncio.run(generate_japan_knowledge_dataset(args.count))
