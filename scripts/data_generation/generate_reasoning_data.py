"""
Generate reasoning and analysis training data using DeepSeek-R1 and Claude
Focus on: Fermi estimation, argumentation, summarization, analysis
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
    ELIOCHAT_SYSTEM_PROMPT, OUTPUT_DIR, REASONING_DATA_PATH, DATA_CONFIG
)

# SSL context for macOS
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# Fermi estimation questions
FERMI_TEMPLATES = [
    "東京都内のコンビニの数を推定してください。",
    "日本全国の自動販売機の数は？",
    "渋谷のスクランブル交差点を1日に何人が渡る？",
    "日本で1年間に消費されるペットボトルの本数は？",
    "東京タワーの重さを推定してください。",
    "新幹線のぞみ号が1年間に運ぶ乗客数は？",
    "日本の小学生の数を推定してください。",
    "東京ドームにゴルフボールは何個入る？",
    "日本で毎日食べられるおにぎりの数は？",
    "地球上の砂粒の数を推定してください。",
    "日本の美容院の数は？",
    "1年間に日本で発行される本の冊数は？",
    "富士山の体積を推定してください。",
    "東京23区の人口密度を推定して。",
    "日本の電車の総走行距離（1日）は？",
]

# Argumentation and debate topics
ARGUMENT_TEMPLATES = [
    "リモートワークのメリットとデメリットを論じてください。",
    "AIが仕事を奪うという意見に賛成ですか、反対ですか？",
    "ベーシックインカムは導入すべきか議論してください。",
    "少子化対策として何が最も効果的か論じてください。",
    "原子力発電の是非について、両論を示してください。",
    "SNSは社会にとって良いものか悪いものか。",
    "英語教育は小学校から始めるべきか。",
    "現金とキャッシュレス、どちらが優れているか。",
    "夏休みの宿題は必要か不要か。",
    "電気自動車は本当に環境に良いのか。",
    "大学教育は無償化すべきか。",
    "週休3日制は導入すべきか。",
    "選挙権の年齢を16歳に引き下げるべきか。",
    "ペットショップでの生体販売は禁止すべきか。",
    "タバコの完全禁止は実施すべきか。",
]

# Analysis and explanation questions
ANALYSIS_TEMPLATES = [
    "日本経済の課題を3つ挙げて説明してください。",
    "なぜ日本では少子高齢化が進んでいるのか分析してください。",
    "スマートフォンが社会に与えた影響を分析してください。",
    "コンビニが成功した理由を分析してください。",
    "日本の教育システムの特徴と課題を説明してください。",
    "クラウドコンピューティングの仕組みを説明してください。",
    "ブロックチェーンの基本原理を解説してください。",
    "機械学習とディープラーニングの違いを説明してください。",
    "なぜ円安が進んでいるのか説明してください。",
    "サブスクリプションビジネスモデルの特徴を分析してください。",
    "プログラミング教育が必修化された背景を説明してください。",
    "SDGsとは何か、企業にとっての意義を説明してください。",
    "メタバースの可能性と課題を分析してください。",
    "生成AIが社会に与える影響を分析してください。",
    "日本の観光産業の強みと弱みを分析してください。",
]

# Summarization tasks
SUMMARIZATION_TEMPLATES = [
    "以下の長文を3行で要約してください。\n\n{text}",
    "この内容を子供でもわかるように説明してください。\n\n{text}",
    "重要なポイントを箇条書きで3つ抽出してください。\n\n{text}",
]

# Sample texts for summarization
SAMPLE_TEXTS = [
    """人工知能（AI）は近年急速に発展し、私たちの生活に大きな影響を与えています。
特に自然言語処理の分野では、GPTやBERTなどの大規模言語モデルの登場により、
機械が人間のように文章を理解し生成することが可能になりました。
これにより、翻訳、要約、対話システムなど多くのアプリケーションが実用化されています。
一方で、AIの倫理的な問題や、雇用への影響、プライバシーの懸念など、
解決すべき課題も多く残されています。""",

    """持続可能な開発目標（SDGs）は、2015年に国連で採択された17の目標です。
貧困の撲滅、質の高い教育、ジェンダー平等、気候変動への対策など、
幅広い分野での目標が設定されています。
企業においても、ESG投資の拡大やサステナビリティ報告の義務化など、
SDGsへの取り組みが経営の重要課題となっています。
日本政府も「SDGsアクションプラン」を策定し、官民一体での推進を図っています。""",

    """量子コンピュータは、量子力学の原理を利用した次世代のコンピュータです。
従来のコンピュータが0と1のビットで計算するのに対し、
量子コンピュータは0と1の重ね合わせ状態（量子ビット）を利用します。
これにより、特定の問題では従来のコンピュータより圧倒的に高速な計算が可能です。
暗号解読、創薬、金融シミュレーション、最適化問題など、
多くの分野での応用が期待されています。""",

    """働き方改革は、日本の労働環境を改善するための取り組みです。
長時間労働の是正、多様で柔軟な働き方の実現、同一労働同一賃金の推進が主な柱です。
2019年には働き方改革関連法が施行され、残業時間の上限規制や
有給休暇の取得義務化などが法制化されました。
コロナ禍をきっかけにリモートワークが普及し、
場所や時間にとらわれない働き方が広がっています。""",

    """5G（第5世代移動通信システム）は、従来の4Gと比べて
高速・大容量、低遅延、多数同時接続という特徴を持ちます。
理論上の最高速度は20Gbpsで、4Gの約100倍です。
遅延は1ミリ秒以下と、ほぼリアルタイムの通信が可能になります。
これにより、自動運転、遠隔医療、スマートファクトリーなど、
新しいサービスやビジネスの創出が期待されています。""",
]

# Critical thinking questions
CRITICAL_THINKING_TEMPLATES = [
    "「若者の活字離れ」は本当に起きているのか、批判的に検討してください。",
    "「日本人は働きすぎ」という説を検証してください。",
    "「AIに仕事を奪われる」という主張の妥当性を評価してください。",
    "「現金主義の日本」という見方は正しいか分析してください。",
    "「日本の英語教育は失敗」という意見を検討してください。",
    "「テレビは終わった」という見方について論じてください。",
    "「ゆとり教育は失敗だった」という評価は妥当か。",
    "「終身雇用は崩壊した」という見方を検証してください。",
    "「日本の医療は世界一」という主張を批判的に検討してください。",
    "「SNSが民主主義を脅かす」という見方について論じてください。",
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
    """Format response with proper <think> tags for reasoning tasks"""
    if "<think>" in raw_response and "</think>" in raw_response:
        return raw_response

    # Generate appropriate thinking based on question type
    thinking_parts = []

    if any(word in question for word in ["推定", "数", "何人", "何個"]):
        thinking_parts.append("フェルミ推定を行う")
        thinking_parts.append("まず大きな枠組みから考える")
        thinking_parts.append("妥当な仮定を置いて計算する")
    elif any(word in question for word in ["メリット", "デメリット", "賛成", "反対", "べきか"]):
        thinking_parts.append("両方の立場を検討する")
        thinking_parts.append("それぞれの根拠を整理する")
        thinking_parts.append("バランスの取れた結論を導く")
    elif any(word in question for word in ["分析", "説明", "理由", "なぜ"]):
        thinking_parts.append("問題の背景を整理する")
        thinking_parts.append("主要な要因を特定する")
        thinking_parts.append("論理的に説明する")
    elif any(word in question for word in ["要約", "まとめ", "ポイント"]):
        thinking_parts.append("テキストの主要な論点を把握する")
        thinking_parts.append("重要度に応じて情報を整理する")
        thinking_parts.append("簡潔にまとめる")
    elif any(word in question for word in ["検証", "批判的", "妥当性"]):
        thinking_parts.append("主張の前提を確認する")
        thinking_parts.append("根拠となるデータを検討する")
        thinking_parts.append("反論の余地がないか検討する")
    else:
        thinking_parts.append("質問の意図を理解する")
        thinking_parts.append("必要な情報を整理する")
        thinking_parts.append("論理的に回答する")

    thinking = "\n".join(thinking_parts)
    return f"<think>\n{thinking}\n</think>\n\n{raw_response}"


def generate_summarization_question() -> str:
    """Generate a summarization question with sample text"""
    template = random.choice(SUMMARIZATION_TEMPLATES)
    text = random.choice(SAMPLE_TEXTS)
    return template.format(text=text)


async def generate_single_example(
    session: aiohttp.ClientSession,
    template_type: str,
    template: str,
    model_key: str,
    semaphore: asyncio.Semaphore
) -> Dict | None:
    """Generate a single training example"""
    if template_type == "summarization":
        question = generate_summarization_question()
    else:
        question = template

    messages = [
        {
            "role": "system",
            "content": """あなたは優秀な分析・推論の専門家です。
質問に対して、まず思考過程を示してから答えを出してください。
- フェルミ推定では、仮定と計算過程を明確に示してください
- 議論では、両方の立場を公平に検討してください
- 分析では、論理的で構造化された説明をしてください
- 要約では、核心を捉えた簡潔なまとめをしてください
思考過程は日本語で丁寧に説明してください。"""
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


async def generate_reasoning_dataset(target_count: int = 10500):
    """Generate the full reasoning dataset"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Template distribution
    templates = {
        "fermi": FERMI_TEMPLATES,
        "argument": ARGUMENT_TEMPLATES,
        "analysis": ANALYSIS_TEMPLATES,
        "summarization": ["summarization"],  # Special handling
        "critical": CRITICAL_THINKING_TEMPLATES,
    }

    # Rate limiting: 10 concurrent requests
    semaphore = asyncio.Semaphore(10)

    examples = []

    # Use SSL context for macOS compatibility
    connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        template_types = list(templates.keys())

        for i in range(target_count):
            # Rotate through template types
            template_type = template_types[i % len(template_types)]
            template_list = templates[template_type]

            if template_type == "summarization":
                template = "summarization"
            else:
                template = random.choice(template_list)

            # Alternate between models
            model_key = "deepseek_r1" if i % 2 == 0 else "claude"
            tasks.append(generate_single_example(
                session, template_type, template, model_key, semaphore
            ))

        # Execute with progress bar
        print(f"Generating {target_count} reasoning examples...")
        results = await tqdm.gather(*tasks, desc="Reasoning Data")

        # Filter out None results
        examples = [r for r in results if r is not None]

    # Save to file
    with open(REASONING_DATA_PATH, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"Generated {len(examples)} examples, saved to {REASONING_DATA_PATH}")
    return examples


if __name__ == "__main__":
    target = DATA_CONFIG["reasoning"]["count"]
    asyncio.run(generate_reasoning_dataset(target))
