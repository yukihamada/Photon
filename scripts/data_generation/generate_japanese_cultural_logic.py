"""
Generate Japanese cultural logic training data
日本的な賢さを持たせるための文化的論理問題データセット
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

CULTURAL_LOGIC_PATH = f"{OUTPUT_DIR}/japanese_cultural_logic.jsonl"

# Category 1: 社会規範とマナーの論理（Cultural Logic）
CULTURAL_LOGIC_SCENARIOS = [
    # 上座・下座の推論
    {
        "category": "上座下座",
        "prompt": """上座・下座に関する問題を作成してください。以下の形式で出力してください：

【質問】具体的なシチュエーション（タクシー、エレベーター、会議室、飲み会など）で複数人の席順を決める問題

【思考プロセス】
<think>
1. 登場人物の序列を整理
2. 場所特有の上座ルールを確認
3. 例外やTPOを考慮
4. 最終的な座席配置を決定
</think>

【回答】正しい座席配置とその理由

例：部長、課長、新入社員、取引先の社長が会議室に入る場合の席順など
毎回異なる人物構成と場所（和室、料亭、新幹線、エレベーター等）で作成してください。"""
    },
    # 親族呼称と冠婚葬祭
    {
        "category": "親族関係",
        "prompt": """日本の親族関係と冠婚葬祭に関する論理問題を作成してください。以下の形式で出力してください：

【質問】複雑な親族関係（義理の関係含む）における呼称や、結婚式・葬儀での役割・ご祝儀・香典の相場を推論する問題

【思考プロセス】
<think>
1. 親族関係の整理（〇〇の△△は私にとって？）
2. 民法上の親族範囲の確認
3. 社会的慣習の考慮
4. 結論の導出
</think>

【回答】親族呼称や適切な対応

例：姉の夫の弟の結婚式に出席すべきか、いとこの配偶者の祖父の葬儀の香典相場など
毎回異なる関係性で作成してください。"""
    },
    # 贈答の論理
    {
        "category": "贈答マナー",
        "prompt": """日本の贈答マナーに関する論理問題を作成してください。以下の形式で出力してください：

【質問】お中元、お歳暮、内祝い、引き出物、快気祝いなどの適切な贈り方・金額・タイミング・のしの書き方を推論する問題

【思考プロセス】
<think>
1. 贈答の種類と目的を確認
2. 相手との関係性を考慮
3. 適切な金額帯・品物を検討
4. のし紙・表書きを決定
</think>

【回答】適切な対応

例：上司の新築祝いにいくら包むべきか、お見舞いにタブーな品物など"""
    }
]

# Category 2: ハイコンテクスト・「空気を読む」推論
HIGH_CONTEXT_SCENARIOS = [
    # 京都風の遠回し表現
    {
        "category": "京都風表現",
        "prompt": """「京都風」の遠回しな表現（いけず）に関する問題を作成してください。以下の形式で出力してください：

【質問】一見褒め言葉や普通の会話に見えるが、実は皮肉や苦情を含む発言の真意を読み解く問題

【思考プロセス】
<think>
1. 文字通りの意味を確認
2. ハイコンテクスト文化での解釈を考慮
3. 隠された真意を推論
4. 適切な対応策を導出
</think>

【回答】発言の真意と適切な対応

例：
「お子さん、元気でよろしいですなぁ」→ 子供がうるさい
「ぶぶ漬けでもどうですか」→ もう帰ってほしい
このような日本的な婉曲表現を毎回新しく作成してください。"""
    },
    # ビジネス婉曲表現
    {
        "category": "ビジネス婉曲表現",
        "prompt": """日本のビジネスシーンでの婉曲表現に関する問題を作成してください。以下の形式で出力してください：

【質問】商談、面接、会議などでよく使われる曖昧な表現の真意を読み解く問題

【思考プロセス】
<think>
1. 表面的な意味を確認
2. ビジネス文化での慣習を考慮
3. 状況証拠から真意を推論
4. 次に取るべきアクションを決定
</think>

【回答】発言の真意と今後の予測

例：
「検討します」「善処します」「持ち帰って相談します」→ 大体お断り
「弊社にはもったいないです」「能力が高すぎます」→ 不採用の婉曲表現
毎回異なるビジネスシーンで作成してください。"""
    },
    # 日常会話の空気読み
    {
        "category": "日常の空気読み",
        "prompt": """日常会話における「空気を読む」問題を作成してください。以下の形式で出力してください：

【質問】飲み会の誘い、デートの断り、友人間のやりとりなどで、言葉の裏にある真意を読み解く問題

【思考プロセス】
<think>
1. 発言の表面的意味を確認
2. 声のトーン・状況・関係性を考慮
3. 日本文化での非言語的サインを分析
4. 真意を推論
</think>

【回答】発言の真意

例：
「今度ご飯行こうね！」→ 社交辞令の可能性
「ちょっと考えさせて」→ 断りの前置き
「大丈夫、気にしないで」→ 本当は気にしている"""
    }
]

# Category 3: 言語構造上の論理
LINGUISTIC_LOGIC_SCENARIOS = [
    # 敬語による動作主特定
    {
        "category": "敬語論理",
        "prompt": """敬語から動作主を特定する問題を作成してください。以下の形式で出力してください：

【質問】尊敬語・謙譲語・丁寧語が混在する会話から、誰が何をしたかを論理的に特定する問題

【思考プロセス】
<think>
1. 各表現が尊敬語か謙譲語かを判別
2. 尊敬語は「相手/目上の動作」
3. 謙譲語は「自分/身内の動作」
4. 動作主を特定
</think>

【回答】動作主と根拠

例：
A「部長は既にご出発されましたか？」
B「はい、先ほど参りました」
→ 「参る」は謙譲語なのでBの動作ではなく...（複雑なパターンを作成）"""
    },
    # 助詞の論理的含意
    {
        "category": "助詞論理",
        "prompt": """「は」と「が」など助詞の使い分けによる意味の違いを推論する問題を作成してください。以下の形式で出力してください：

【質問】同じ文で助詞だけが異なる2つの文を比較し、意味やニュアンスの違いを論理的に説明する問題

【思考プロセス】
<think>
1. 「は」は主題提示・対比のニュアンス
2. 「が」は排他・新情報の焦点
3. 文脈での使い分けを分析
4. 意味の違いを特定
</think>

【回答】それぞれの文が持つニュアンスの違い

例：
「私は知らない」vs「私が知らない」
「水が飲みたい」vs「水は飲みたい」"""
    },
    # 主語省略の推論
    {
        "category": "主語省略",
        "prompt": """日本語の主語省略から文脈を推論する問題を作成してください。以下の形式で出力してください：

【質問】主語が省略された複数の文から、誰が何について話しているかを推論する問題

【思考プロセス】
<think>
1. 省略された主語を文脈から推測
2. 動詞の自他、授受表現からヒントを得る
3. 敬語レベルから関係性を推測
4. 全体の意味を構築
</think>

【回答】省略されていた主語と文の意味

例：長文の会話で「〜してくれた」「〜してもらった」「〜してあげた」が混在"""
    }
]

# Category 4: ブラジリアン柔術（物理法則と因果関係の論理）
BJJ_SCENARIOS = [
    # フレーム理論とエスケープ
    {
        "category": "BJJ物理論理",
        "prompt": """ブラジリアン柔術のエスケープ（脱出）に関する物理的論理問題を作成してください。以下の形式で出力してください：

【質問】サイドコントロール、マウント、バックコントロールなどの不利なポジションからの脱出方法を、物理法則（テコの原理、フレーム構造、重心）に基づいて説明する問題

【思考プロセス】
<think>
1. 現在のポジションと問題点を分析
2. 選択肢Aと選択肢Bの物理的効果を比較
3. 「スペース」「フレーム」「重心移動」の観点から評価
4. 最適解を導出
</think>

【回答】物理的に正しい技術選択とその理由

例：サイドコントロールで相手をハグするvs.フレームを作る
毎回異なるポジションと技術で作成してください。"""
    },
    # アクション・リアクションの連鎖
    {
        "category": "BJJ因果連鎖",
        "prompt": """ブラジリアン柔術の「アクション・リアクション」に関する問題を作成してください。以下の形式で出力してください：

【質問】ある技を仕掛けた時に相手が特定の反応をした場合、その反作用を利用して次に狙うべき技を推論する問題

【思考プロセス】
<think>
1. 最初に仕掛けた技と目的を確認
2. 相手の反応（エネルギーの方向）を分析
3. その反応によって生まれる隙・弱点を特定
4. 相手の力の流れを利用した次の技を選択
</think>

【回答】次に狙うべき技とその物理的理由

例：ヒップスローを耐えられた→ギロチンチョーク
相手が引いたら押し、押してきたら引く、の原則"""
    },
    # ポジショナルヒエラルキー
    {
        "category": "BJJポジション論理",
        "prompt": """BJJのポジショナルヒエラルキー（ポジションの優劣）に関する問題を作成してください。以下の形式で出力してください：

【質問】2つのポジションを比較し、どちらが有利かを論理的に説明する問題、またはポジション改善の最適ルートを推論する問題

【思考プロセス】
<think>
1. 各ポジションの特徴（コントロール度、サブミッション可能性、エスケープ難易度）を分析
2. ポイント制での評価を確認
3. リスク/リターンを比較
4. 最適な判断を導出
</think>

【回答】ポジションの優劣判断と根拠

例：サイドコントロールvsニーオンベリー、クローズドガードvsオープンガード"""
    }
]

# Category 5: ポーカー（確率と期待値の論理）
POKER_SCENARIOS = [
    # ポットオッズと期待値
    {
        "category": "ポーカー期待値",
        "prompt": """ポーカー（テキサスホールデム）のポットオッズと期待値に関する問題を作成してください。以下の形式で出力してください：

【質問】具体的なポット額、ベット額、推定勝率が与えられた状況でコール/フォールド/レイズの判断を数学的に求める問題

【思考プロセス】
<think>
1. コストの計算（コールに必要な額）
2. リターンの計算（勝った場合の獲得額）
3. ポットオッズの計算（必要勝率）
4. 実際の勝率との比較
5. 期待値（EV）がプラスかマイナスかを判定
</think>

【回答】数学的に正しい判断とその計算過程

毎回異なる数値（ポット額100-500ドル、ベット額、勝率5-50%など）で作成してください。"""
    },
    # レンジリーディング
    {
        "category": "ポーカーレンジ推測",
        "prompt": """ポーカーにおけるレンジリーディング（相手の手札範囲の推測）問題を作成してください。以下の形式で出力してください：

【質問】相手のベッティングパターン、プレイヤータイプ、ボードの状況から相手の持っている手札範囲を絞り込む問題

【思考プロセス】
<think>
1. 相手のプレイヤータイプを確認（タイト/ルース、アグレッシブ/パッシブ）
2. プリフロップのアクションから手札範囲を推測
3. ボードのカードと相手の反応の整合性を確認
4. 矛盾点から手札範囲を絞り込む
</think>

【回答】相手が持っている可能性が高い手札とその根拠

例：タイトなプレイヤーがプリフロップでレイズしたがAが出て弱気に→KK,QQの可能性大"""
    },
    # ブラフとバリューの論理
    {
        "category": "ポーカーブラフ論理",
        "prompt": """ポーカーにおけるブラフとバリューベットの論理問題を作成してください。以下の形式で出力してください：

【質問】特定の状況（自分の手札、ボード、相手のタイプ）でブラフすべきか、バリューベットすべきか、チェックすべきかを論理的に判断する問題

【思考プロセス】
<think>
1. 自分の手札の強さを評価
2. 相手のレンジ（持っている可能性のある手札）を推測
3. 相手のコール頻度・フォールド頻度を考慮
4. ブラフの成功率×利益 vs バリューベットの期待値を比較
5. 最適なアクションを選択
</think>

【回答】最適なアクションとその戦略的理由"""
    }
]

# All scenarios combined
ALL_SCENARIOS = (
    CULTURAL_LOGIC_SCENARIOS +
    HIGH_CONTEXT_SCENARIOS +
    LINGUISTIC_LOGIC_SCENARIOS +
    BJJ_SCENARIOS +
    POKER_SCENARIOS
)


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
            "temperature": 0.85,
            "max_tokens": 2000,
        }

        try:
            async with session.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=180)
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


def parse_cultural_content(raw: str, category: str) -> Dict | None:
    """Parse cultural logic content into training format"""
    if not raw:
        return None

    # Extract question
    question = None
    answer = None

    # Look for question patterns
    q_markers = ["【質問】", "質問:", "問題:"]
    for marker in q_markers:
        if marker in raw:
            parts = raw.split(marker, 1)
            if len(parts) > 1:
                rest = parts[1]
                # Find where answer starts
                for a_marker in ["【思考プロセス】", "【回答】", "<think>", "思考プロセス:"]:
                    if a_marker in rest:
                        question = rest.split(a_marker)[0].strip()
                        break
                if not question:
                    question = rest.split("\n\n")[0].strip()
                break

    # Extract the full response with <think> tags
    if "<think>" in raw and "</think>" in raw:
        # Find the think section and what follows
        think_start = raw.find("<think>")
        think_end = raw.find("</think>") + len("</think>")

        if think_start > 0 and think_end > think_start:
            think_content = raw[think_start:think_end]
            # Get the answer after </think>
            after_think = raw[think_end:].strip()

            # Clean up answer
            for marker in ["【回答】", "回答:"]:
                if marker in after_think:
                    after_think = after_think.split(marker, 1)[1].strip()
                    break

            # Remove any final markers
            answer_text = after_think.split("---")[0].strip()
            if answer_text:
                answer = f"{think_content}\n\n{answer_text}"

    if not question or not answer:
        # Try alternative parsing
        if "<think>" in raw:
            lines = raw.strip().split("\n")
            for i, line in enumerate(lines):
                if "?" in line or "か？" in line or "ください" in line:
                    question = line.strip()
                    break

            if "<think>" in raw:
                answer = raw[raw.find("<think>"):].strip()

    if not question or not answer:
        return None

    # Validate
    if len(question) < 20 or "<think>" not in answer:
        return None

    return {
        "messages": [
            {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ],
        "category": category
    }


async def generate_cultural_example(
    session: aiohttp.ClientSession,
    scenario: Dict,
    semaphore: asyncio.Semaphore
) -> Dict | None:
    """Generate a single cultural logic example"""
    category = scenario["category"]
    prompt = scenario["prompt"]

    system_prompt = """あなたは日本の文化、商習慣、ハイコンテクストなコミュニケーションの達人です。
日本語学習者がつまずきやすい「文字通りの意味と真意が違う状況」や「日本のビジネスマナーに基づく論理パズル」を作成してください。

重要な指示:
1. 必ず【質問】と【思考プロセス】と【回答】を含めてください
2. 思考プロセスは必ず<think>タグで囲んでください
3. 毎回異なる具体的なシチュエーションを作成してください
4. 日本文化の深い理解に基づいた論理的推論を含めてください
5. 外国人が驚くような「日本ならではの論理」を扱ってください"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # Use Claude for more nuanced cultural understanding
    model = MODELS["claude"] if random.random() > 0.3 else MODELS["deepseek_r1"]
    response = await call_openrouter(session, model, messages, semaphore)

    if response:
        return parse_cultural_content(response, category)
    return None


async def generate_cultural_dataset(target_count: int = 200):
    """Generate Japanese cultural logic dataset"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(8)
    examples = []

    connector = aiohttp.TCPConnector(ssl=SSL_CONTEXT)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []

        # Distribute scenarios evenly
        for i in range(target_count):
            scenario = ALL_SCENARIOS[i % len(ALL_SCENARIOS)]
            tasks.append(generate_cultural_example(session, scenario, semaphore))

        print(f"Generating {target_count} Japanese cultural logic examples...")
        results = await tqdm.gather(*tasks, desc="Cultural Logic")

        examples = [r for r in results if r is not None]

    # Save
    with open(CULTURAL_LOGIC_PATH, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    # Print category distribution
    categories = {}
    for ex in examples:
        cat = ex.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\nGenerated {len(examples)} examples, saved to {CULTURAL_LOGIC_PATH}")
    print("Category distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    return examples


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=200)
    args = parser.parse_args()
    asyncio.run(generate_cultural_dataset(args.count))
