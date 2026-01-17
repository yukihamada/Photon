"""
Generate logic and math training data using DeepSeek-R1 and Qwen-Math
Focus on: mathematics, coding, logic puzzles, power calculations
"""
import json
import asyncio
import aiohttp
import ssl
import certifi
import random
from pathlib import Path
from typing import List, Dict, Any
from tqdm.asyncio import tqdm
import sys
sys.path.append(str(Path(__file__).parent))
from config import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODELS,
    ELIOCHAT_SYSTEM_PROMPT, OUTPUT_DIR, LOGIC_DATA_PATH, DATA_CONFIG
)

# SSL context for macOS
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# Question templates for logic/math
MATH_TEMPLATES = [
    # Power calculations (critical - fixing 2^10 errors)
    "2の{n}乗を計算してください。",
    "{base}の{exp}乗はいくつですか？",
    "2^{n}を求めてください。",
    # Basic arithmetic
    "{a} + {b} × {c} を計算してください。",
    "{a} ÷ {b} × {c} の答えは？",
    "({a} + {b}) × {c} - {d} を計算してください。",
    # Fractions
    "{a}/{b} + {c}/{d} を計算してください。",
    "{a}/{b} × {c}/{d} の答えは？",
    # Percentages
    "{a}の{p}%はいくつですか？",
    "{a}円の商品が{p}%オフになると、いくらですか？",
    # Sequences
    "1, 2, 4, 8, 16, ... の次の数は？",
    "フィボナッチ数列の{n}番目は？",
    # Word problems
    "りんごが{a}個あります。{b}個食べたら残りは何個？",
    "{a}人で{b}円を均等に分けると、一人いくら？",
    # Algebra
    "x + {a} = {b} のとき、x は？",
    "{a}x + {b} = {c} を解いてください。",
    # Geometry
    "半径{r}cmの円の面積は？（円周率はπ）",
    "一辺{a}cmの正方形の対角線の長さは？",
    # Statistics
    "{nums} の平均値は？",
    "{nums} の中央値と最頻値は？",
    # Logic puzzles
    "AはBより大きく、BはCより大きい。最も小さいのは？",
    "全ての猫は動物です。タマは猫です。タマは動物ですか？",
]

CODING_TEMPLATES = [
    "Pythonで1から{n}までの合計を求めるコードを書いてください。",
    "リスト {nums} をソートするPythonコードは？",
    "フィボナッチ数列の第{n}項を求める関数を書いてください。",
    "素数判定を行うPython関数を書いてください。",
    "二分探索のアルゴリズムを説明してください。",
    "再帰を使って{n}の階乗を計算する関数を書いてください。",
    "文字列を逆順にするPythonの方法は？",
    "リスト内の重複を削除するには？",
    "辞書をソートする方法を教えてください。",
    "正規表現でメールアドレスを検証するパターンは？",
]

LOGIC_TEMPLATES = [
    "3つの箱があり、1つだけに当たりが入っています。Aを選んだ後、司会者がBを開けてハズレを見せました。変えるべき？",
    "「この文は偽である」というパラドックスを説明してください。",
    "5人が一列に並ぶ方法は何通り？",
    "6人から3人を選ぶ組み合わせは？",
    "コインを{n}回投げて、すべて表が出る確率は？",
    "赤玉{r}個、白玉{w}個から2個取り出すとき、両方赤の確率は？",
    "AとBが同時に仕事をすると{d}日で終わる。Aだけだと{a}日。Bだけだと何日？",
    "時速{v}kmで{t}時間走ると何km進む？",
    "3の倍数かつ5の倍数である100以下の正の整数は？",
    "1から100までの整数の中で、3の倍数はいくつある？",
]


def generate_random_params():
    """Generate random parameters for templates"""
    return {
        "n": random.randint(2, 15),
        "base": random.choice([2, 3, 5, 10]),
        "exp": random.randint(2, 10),
        "a": random.randint(1, 100),
        "b": random.randint(1, 50),
        "c": random.randint(1, 30),
        "d": random.randint(1, 20),
        "p": random.choice([10, 15, 20, 25, 30, 50]),
        "r": random.randint(1, 20),
        "w": random.randint(1, 20),
        "v": random.choice([60, 80, 100, 120]),
        "t": random.randint(1, 5),
        "nums": str(random.sample(range(1, 100), random.randint(3, 7))),
    }


def format_question(template: str, params: dict) -> str:
    """Format a question template with random parameters"""
    try:
        return template.format(**params)
    except KeyError:
        return template


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
                timeout=aiohttp.ClientTimeout(total=60)
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
    # If response already has thinking tags, clean it up
    if "<think>" in raw_response and "</think>" in raw_response:
        return raw_response

    # Extract any reasoning if present (DeepSeek-R1 often includes reasoning)
    if "。理由：" in raw_response or "なぜなら" in raw_response or "考え方：" in raw_response:
        parts = raw_response.split("。", 1)
        if len(parts) > 1:
            thinking = parts[1].strip()
            answer = parts[0].strip()
            return f"<think>\n{thinking}\n</think>\n\n{answer}"

    # Generate thinking based on question type
    thinking_parts = []

    if any(word in question for word in ["乗", "^", "累乗", "べき乗"]):
        thinking_parts.append("累乗の計算を順番に行う")
        thinking_parts.append("ステップバイステップで計算していく")
    elif any(word in question for word in ["+", "-", "×", "÷", "計算"]):
        thinking_parts.append("演算の優先順位を確認する")
        thinking_parts.append("順番に計算を進める")
    elif any(word in question for word in ["確率", "組み合わせ", "並べ方"]):
        thinking_parts.append("場合の数を考える")
        thinking_parts.append("公式を適用する")
    elif any(word in question for word in ["コード", "関数", "プログラム"]):
        thinking_parts.append("必要な処理を整理する")
        thinking_parts.append("適切なアルゴリズムを選ぶ")
    else:
        thinking_parts.append("問題を整理する")
        thinking_parts.append("解法を考える")

    thinking = "\n".join(thinking_parts)
    return f"<think>\n{thinking}\n</think>\n\n{raw_response}"


async def generate_single_example(
    session: aiohttp.ClientSession,
    template: str,
    model_key: str,
    semaphore: asyncio.Semaphore
) -> Dict | None:
    """Generate a single training example"""
    params = generate_random_params()
    question = format_question(template, params)

    messages = [
        {
            "role": "system",
            "content": """あなたは優秀な数学・論理の先生です。
質問に対して、まず思考過程を示してから答えを出してください。
思考過程は日本語で、ステップバイステップで説明してください。
特に累乗計算（2の10乗など）は、途中の計算も含めて丁寧に示してください。"""
        },
        {
            "role": "user",
            "content": question
        }
    ]

    model = MODELS.get(model_key, MODELS["deepseek_r1"])
    response = await call_openrouter(session, model, messages, semaphore)

    if response:
        formatted_response = format_response_with_thinking(question, response)
        return {
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": formatted_response}
            ]
        }
    return None


async def generate_logic_dataset(target_count: int = 10500):
    """Generate the full logic/math dataset"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Combine all templates
    all_templates = MATH_TEMPLATES + CODING_TEMPLATES + LOGIC_TEMPLATES

    # Rate limiting: 10 concurrent requests
    semaphore = asyncio.Semaphore(10)

    examples = []

    # Use SSL context for macOS compatibility
    connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Create tasks for all examples
        tasks = []
        for i in range(target_count):
            template = random.choice(all_templates)
            # Alternate between models
            model_key = "deepseek_r1" if i % 2 == 0 else "qwen_math"
            tasks.append(generate_single_example(session, template, model_key, semaphore))

        # Execute with progress bar
        print(f"Generating {target_count} logic/math examples...")
        results = await tqdm.gather(*tasks, desc="Logic/Math Data")

        # Filter out None results
        examples = [r for r in results if r is not None]

    # Save to file
    with open(LOGIC_DATA_PATH, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"Generated {len(examples)} examples, saved to {LOGIC_DATA_PATH}")
    return examples


if __name__ == "__main__":
    target = DATA_CONFIG["logic_math"]["count"]
    asyncio.run(generate_logic_dataset(target))
