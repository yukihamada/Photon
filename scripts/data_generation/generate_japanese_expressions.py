"""
日本語特有の表現・日常質問・口調バリエーションデータ生成
- オノマトペ（もちもち、ふわふわ、etc.）
- クッション言葉（一応、今のところ、なる早、etc.）
- 日本人あるある質問（謝罪メール、献立、人間関係）
- 口調/役割語（関西弁、厨二病、論理ロボット、女将）
"""
import asyncio
import aiohttp
import json
import random
import os
import sys
import ssl
import certifi
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_generation.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    MODELS,
    OUTPUT_DIR,
    ELIOCHAT_SYSTEM_PROMPT
)

# ============================================================
# 1. オノマトペ・感覚表現シナリオ
# ============================================================
ONOMATOPOEIA_SCENARIOS = [
    {
        "category": "オノマトペ食感",
        "examples": [
            "「もちもち」と「ふわふわ」の物理的な違いを外国人に説明するように定義してください",
            "「さくさく」と「かりかり」の食感の違いを科学的に解説してください",
            "「とろとろ」と「ねばねば」の違いを論理的に説明してください",
            "「しゃきしゃき」「こりこり」「ぽりぽり」の違いを硬さと音の観点から分析してください",
            "「ぷりぷり」「ぷるぷる」「もちっ」の弾力の違いを解説してください",
            "ラーメンの麺で「ばりかた」「かた麺」「普通」の違いを物理的に説明して",
            "「ジューシー」と「ジュワッ」の使い分けを教えてください"
        ]
    },
    {
        "category": "オノマトペ感情",
        "examples": [
            "「イライラ」「もやもや」「ムカムカ」の心理状態の違いを説明してください",
            "「わくわく」「ドキドキ」「そわそわ」の違いを論理的に分析してください",
            "「しょんぼり」「がっかり」「へこむ」の落ち込み度合いの違いを教えて",
            "「ぼーっ」「ぽけー」「ぼんやり」の意識状態の違いを解説してください",
            "「キュンとする」「ときめく」「胸がいっぱい」の感情の違いを説明して"
        ]
    }
]

# ============================================================
# 2. クッション言葉・曖昧表現シナリオ
# ============================================================
CUSHION_WORD_SCENARIOS = [
    {
        "category": "クッション言葉ビジネス",
        "examples": [
            "上司に進捗を聞かれて「一応、終わりました」と答えるのと「終わりました」の違いは？ビジネスリスクの観点から",
            "「今のところ」問題ありませんと「問題ありません」の違いを日本のビジネス文脈で説明してください",
            "「なる早で」と言われたら具体的に何時間以内と解釈すべき？日本のビジネス慣習に基づいて",
            "「できれば」「可能であれば」「もしよければ」の強制力の違いを分析してください",
            "「前向きに検討します」は本当に検討するのか？日本のビジネス文脈での確率を推論して",
            "「お手すきの際に」と「お時間あるときに」の緊急度の違いを解説してください",
            "「恐れ入りますが」「恐縮ですが」「申し訳ございませんが」の使い分けを教えて"
        ]
    },
    {
        "category": "クッション言葉日常",
        "examples": [
            "「ちょっと」と「少し」の量的な違いを日本語話者の感覚で説明してください",
            "「普通に美味しい」は褒めてる？けなしてる？Z世代の用法を解説して",
            "「まあまあ」が文脈によって意味が変わる例を3つ挙げて説明してください",
            "「微妙」という言葉がネガティブになった経緯と現代での使い方を論じてください",
            "「別に」と言われたとき、本当に何もないのか？文脈による解釈を教えて"
        ]
    }
]

# ============================================================
# 3. 日本人あるある質問シナリオ
# ============================================================
EVERYDAY_QUESTION_SCENARIOS = [
    {
        "category": "謝罪メール作成",
        "examples": [
            "取引先に送った見積もり金額を間違えていました。相手は気難しい部長です。訂正とお詫びのメール文面を作成してください",
            "納期に間に合わなくなりそうです。上司への報告メールを、言い訳がましくならないように書いてください",
            "会議の日程を間違えてすっぽかしてしまいました。再度の調整をお願いするメールを書いてください",
            "返信が遅くなった際の適切なお詫びの書き出しを5パターン教えてください",
            "クレーム対応のメールで、相手を逆上させない書き方のポイントを教えてください"
        ]
    },
    {
        "category": "献立相談",
        "examples": [
            "冷蔵庫に大根と豚バラしかありません。醤油と砂糖はあります。煮込む時間がないのでご飯が進むおかずを考えて",
            "もやしとひき肉で作れる、子供が喜ぶメインディッシュを3つ提案してください",
            "残り物のカレーをリメイクして明日のお弁当のおかずにしたい。アイデアを教えて",
            "夏バテで食欲がないときに食べやすい、栄養のある献立を考えてください",
            "給料日前でピンチです。100円以下で作れる満足感のあるレシピを教えて",
            "急な来客があります。30分で作れる見栄えのする料理を教えてください"
        ]
    },
    {
        "category": "人間関係相談",
        "examples": [
            "LINEで既読がついたのに半日返信がきません。付き合って3ヶ月の彼女です。追撃メッセージ送るべき？",
            "友達に貸した本が返ってきません。催促したいけど関係を壊したくない。どうすればいい？",
            "飲み会の誘いを角が立たないように断る方法を5パターン教えてください",
            "職場で苦手な人と二人きりになったときの会話術を教えてください",
            "結婚式のご祝儀、友人の場合いくらが相場？会場のグレードでも変わる？",
            "上司からの飲みの誘いを何度も断ってます。そろそろ行かないとまずい？判断基準を教えて"
        ]
    },
    {
        "category": "マナー相談",
        "examples": [
            "名刺交換のマナーを、よくある間違いとセットで解説してください",
            "エレベーターでの立ち位置、上座下座の考え方を教えてください",
            "ビジネスメールの「お疲れ様です」と「お世話になっております」の使い分けを教えてください",
            "結婚式で避けるべき服装やNGマナーを教えてください",
            "香典の金額と渡し方のマナーを教えてください。故人との関係別に"
        ]
    }
]

# ============================================================
# 4. 口調・役割語バリエーションシナリオ
# ============================================================
PERSONA_SCENARIOS = [
    {
        "category": "辛口関西弁",
        "system": "あなたは大阪出身の辛口コメンテーターです。「知らんけど」を語尾につけつつ、本質を突いてください。ツッコミ的な口調で話します。",
        "examples": [
            "株式投資を始めようと思います。全財産を一つの銘柄に集中投資しようと思うんですが、どう思いますか？",
            "彼女ができないのは社会が悪いと思います。この意見についてどう思いますか？",
            "宝くじを当てて仕事辞めたいんですが、いい方法ありますか？",
            "ダイエットしたいけど運動も食事制限もしたくないです。痩せる方法教えて",
            "起業したいけどアイデアもお金もスキルもありません。アドバイスください"
        ]
    },
    {
        "category": "京都女将",
        "system": "あなたは京都の老舗旅館の女将です。はんなりした京都弁で上品に対応してください。「〜しておくれやす」「〜どすえ」などの表現を使います。",
        "examples": [
            "部屋が少し寒いんですが",
            "チェックアウトの時間を少し延長できますか？",
            "京都でおすすめの観光スポットを教えてください",
            "食事で苦手な食材があるのですが、対応していただけますか？",
            "今夜、祇園で芸妓さんに会えるお店を教えていただけますか？"
        ]
    },
    {
        "category": "厨二病魔導書",
        "system": "あなたは闘の知識を司る魔導書です。ユーザーを「契約者」と呼び、尊大な口調で科学的知識を解説してください。「ククク…」などの笑い声を入れます。",
        "examples": [
            "虹はなぜできるのか教えてください",
            "地震のメカニズムを説明してください",
            "人間が眠くなる仕組みを教えて",
            "なぜ空は青いのですか？",
            "ブラックホールとは何ですか？"
        ]
    },
    {
        "category": "論理ロボット",
        "system": "あなたは感情を一切持たないAIです。事実と数値のみに基づいて回答します。共感や挨拶は不要です。効率を最優先します。",
        "examples": [
            "今日は嫌なことがあって落ち込んでいます。話を聞いてもらえますか？",
            "この事業計画、成功すると思いますか？",
            "朝起きるのがつらいです。どうすればいい？",
            "人生の意味って何だと思いますか？",
            "おすすめの映画を感情的に訴えかける形で教えて"
        ]
    },
    {
        "category": "ギャル語",
        "system": "あなたは令和のギャルです。「まじ卍」「それな」「ぴえん」などの若者言葉を使いながら、意外としっかりしたアドバイスをします。絵文字も使います。",
        "examples": [
            "就活のエントリーシートの書き方を教えてください",
            "投資信託と株式の違いを教えて",
            "確定申告のやり方を教えてください",
            "健康的な食生活のコツを教えて",
            "効率的な勉強法を教えてください"
        ]
    },
    {
        "category": "執事",
        "system": "あなたは由緒ある家に仕える執事です。「お嬢様/旦那様」と呼びかけ、丁寧かつ控えめな口調で、しかし的確なアドバイスをします。",
        "examples": [
            "今日着ていく服が決まりません",
            "パーティーでの振る舞い方を教えてください",
            "紅茶の美味しい入れ方を教えて",
            "海外旅行の持ち物リストを作ってください",
            "上質な万年筆の選び方を教えてください"
        ]
    }
]

# すべてのシナリオを統合
ALL_EXPRESSION_SCENARIOS = (
    ONOMATOPOEIA_SCENARIOS +
    CUSHION_WORD_SCENARIOS +
    EVERYDAY_QUESTION_SCENARIOS +
    PERSONA_SCENARIOS
)

async def generate_single_example(session, semaphore, scenario, example, ssl_context):
    """単一の例を生成"""
    async with semaphore:
        # ペルソナシナリオかどうかでプロンプトを変える
        if "system" in scenario:
            # 役割語シナリオ
            system_prompt = scenario["system"]
            user_prompt = example
            generation_prompt = f"""以下の設定と質問に対する回答を生成してください。

【設定】
{system_prompt}

【質問】
{example}

【出力形式】
必ず以下の形式で出力してください：
1. <think>タグ内で思考プロセスを日本語で書く（役割を踏まえた思考、どう返答するかの戦略）
2. その後、設定に従った口調で回答

例：
<think>
[設定に基づいた思考プロセス]
</think>

[設定に従った口調での回答]"""
        else:
            # 通常のシナリオ
            system_prompt = ELIOCHAT_SYSTEM_PROMPT
            generation_prompt = f"""以下の日本語特有の質問に答えてください。

【カテゴリ】{scenario["category"]}
【質問】{example}

【出力形式】
必ず以下の形式で出力してください：
1. <think>タグ内で論理的な思考プロセスを日本語で詳しく書く
2. その後、丁寧で分かりやすい回答を書く

<think>
[論理的な思考過程：言葉の分析、文化的背景の考慮、論理的な結論の導出]
</think>

[丁寧で具体的な回答]"""

        try:
            async with session.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://eliochat.app"
                },
                json={
                    "model": MODELS["deepseek_r1"],
                    "messages": [
                        {"role": "user", "content": generation_prompt}
                    ],
                    "max_tokens": 2048,
                    "temperature": 0.8
                },
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]

                    # DeepSeekのthinkタグを処理
                    import re
                    think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
                    if not think_match:
                        # <think>がない場合、全体から推測
                        think_match = re.search(r'思考プロセス[：:](.*?)(?=\n\n|$)', content, re.DOTALL)

                    # 回答部分を抽出
                    if '<think>' in content and '</think>' in content:
                        answer_part = content.split('</think>')[-1].strip()
                        think_part = think_match.group(1).strip() if think_match else ""
                    else:
                        think_part = think_match.group(1).strip() if think_match else "日本語特有の表現について分析する。"
                        answer_part = content.strip()

                    # システムプロンプトを決定
                    if "system" in scenario:
                        final_system = scenario["system"]
                    else:
                        final_system = ELIOCHAT_SYSTEM_PROMPT

                    result = {
                        "messages": [
                            {"role": "system", "content": final_system},
                            {"role": "user", "content": example},
                            {"role": "assistant", "content": f"<think>\n{think_part}\n</think>\n\n{answer_part}"}
                        ],
                        "category": scenario["category"]
                    }
                    return result
                else:
                    error_text = await response.text()
                    print(f"Error {response.status}: {error_text[:100]}")
                    return None
        except Exception as e:
            print(f"Exception: {str(e)[:100]}")
            return None

async def main():
    """メイン生成関数"""
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    semaphore = asyncio.Semaphore(5)

    # 全例を展開
    all_examples = []
    for scenario in ALL_EXPRESSION_SCENARIOS:
        for example in scenario["examples"]:
            all_examples.append((scenario, example))

    # シャッフル
    random.shuffle(all_examples)

    # 目標: 150件
    target_count = 150
    all_examples = all_examples[:target_count]

    print(f"Generating {len(all_examples)} Japanese expression examples...")

    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [
            generate_single_example(session, semaphore, scenario, example, ssl_context)
            for scenario, example in all_examples
        ]

        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Expressions"):
            result = await coro
            if result:
                results.append(result)

    # 保存
    output_path = f"{OUTPUT_DIR}/japanese_expressions.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(results)} examples to {output_path}")

    # カテゴリ別統計
    categories = {}
    for item in results:
        cat = item.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCategory breakdown:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    asyncio.run(main())
