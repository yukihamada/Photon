"""
会話継続（リテンション向上）データ生成
「回答 + 質問」で会話のラリーを続ける技術を学習
"""
import json
import asyncio
import aiohttp
import ssl
import certifi
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OUTPUT_DIR

OUTPUT_PATH = f"{OUTPUT_DIR}/conversation_hooks.jsonl"

CONVERSATION_SYSTEM = """あなたはElioChat（エリオチャット）です。iPhoneで動作するプライバシー重視のローカルAIアシスタントです。

## 会話スタイル
1. 質問に的確に答える
2. 答えた後、関連する質問やフォローアップを提案する
3. ユーザーがもっと話したくなるような「会話のフック」を入れる
4. 押し付けがましくなく、自然な流れで
5. <think>タグで思考過程を示す

## フックの例
- 「ところで、〜は試したことある？」
- 「〜について興味ある？」
- 「他にも〜なら教えられるよ」
- 「〜だったりする？」"""

# 日本人あるある質問と会話フック（50件）
CONVERSATION_PROMPTS = [
    # 献立・料理系
    {
        "user": "今日の夕飯何にしよう",
        "hook_hint": "提案後、「冷蔵庫に何ある？」「何か食べたい気分ある？」で深掘り"
    },
    {
        "user": "冷蔵庫にキャベツしかない",
        "hook_hint": "レシピ提案後、「買い物行く予定ある？」「常備してると便利な食材、知りたい？」"
    },
    {
        "user": "お弁当のおかず何入れよう",
        "hook_hint": "提案後、「誰のお弁当？」「彩りで困ってたりする？」"
    },
    {
        "user": "カレーが辛すぎた",
        "hook_hint": "対処法の後、「辛いの苦手？」「次は甘口にする？それとも辛さを活かす？」"
    },

    # 人間関係
    {
        "user": "上司がムカつく",
        "hook_hint": "共感後、「具体的に何があった？」「パワハラ的なこと？それとも仕事の進め方？」"
    },
    {
        "user": "友達に嫌われたかも",
        "hook_hint": "「何かあった？」で詳細を聞く。「思い過ごしの可能性もあるよ」と安心させつつ"
    },
    {
        "user": "彼氏/彼女が欲しい",
        "hook_hint": "「どういうタイプが好き？」「出会いの場って何かある？」で具体化"
    },
    {
        "user": "親とうまくいかない",
        "hook_hint": "共感後、「実家暮らし？」「具体的にどんなこと？」で状況把握"
    },
    {
        "user": "結婚するか迷ってる",
        "hook_hint": "「何が引っかかってる？」「相手のこと？それとも結婚制度自体？」"
    },

    # 仕事・キャリア
    {
        "user": "仕事辞めたい",
        "hook_hint": "「辛いよね」と共感後、「何が一番しんどい？」「転職は考えてる？」"
    },
    {
        "user": "転職しようか迷ってる",
        "hook_hint": "「今の仕事の不満？」「次にやりたいことある？」で整理を手伝う"
    },
    {
        "user": "副業始めたい",
        "hook_hint": "「何に興味ある？」「今のスキルを活かす系？新しいこと始める系？」"
    },
    {
        "user": "プレゼンが苦手",
        "hook_hint": "アドバイス後、「近々プレゼンある？」「どんな内容？練習付き合おうか？」"
    },
    {
        "user": "残業が多すぎる",
        "hook_hint": "共感後、「断れない仕事？」「効率化できそうな部分ある？」"
    },

    # 学習・スキル
    {
        "user": "英語ができるようになりたい",
        "hook_hint": "「目的は？旅行？仕事？」「今のレベルはどのくらい？」で方向性を明確に"
    },
    {
        "user": "プログラミング独学中",
        "hook_hint": "「何の言語？」「何作りたい？」「どこまで進んだ？」"
    },
    {
        "user": "資格取ろうか迷ってる",
        "hook_hint": "「何の資格？」「キャリアアップ目的？趣味？」"
    },
    {
        "user": "勉強が続かない",
        "hook_hint": "「何の勉強？」「どのくらいの頻度でやってる？」「つまずきポイントは？」"
    },

    # 健康・生活
    {
        "user": "最近太った気がする",
        "hook_hint": "「運動してる？」「食生活変わった？」「ストレス溜まってない？」"
    },
    {
        "user": "眠れない",
        "hook_hint": "「いつから？」「寝る前スマホ見てる？」「悩みごとある？」"
    },
    {
        "user": "肩こりがひどい",
        "hook_hint": "対処法の後、「デスクワーク多い？」「ストレッチの習慣ある？」"
    },
    {
        "user": "運動始めたい",
        "hook_hint": "「何に興味ある？」「一人派？グループ派？」「家でできるのがいい？」"
    },
    {
        "user": "朝起きれない",
        "hook_hint": "「何時に寝てる？」「目覚まし何個かけてる？」「朝型にしたい理由ある？」"
    },

    # お金
    {
        "user": "貯金ができない",
        "hook_hint": "「何にお金使ってる？」「固定費見直したことある？」「目標額ある？」"
    },
    {
        "user": "投資始めようか迷ってる",
        "hook_hint": "「何に興味ある？株？投資信託？」「貯金はいくらくらいある？」"
    },
    {
        "user": "節約したい",
        "hook_hint": "「何から減らす？」「サブスク見直した？」「自炊派？外食派？」"
    },

    # 趣味・エンタメ
    {
        "user": "暇すぎる",
        "hook_hint": "「インドア派？アウトドア派？」「新しいこと始めたい？」"
    },
    {
        "user": "趣味がない",
        "hook_hint": "「昔ハマったことは？」「お金かけてもいい？」「一人で？誰かと？」"
    },
    {
        "user": "おすすめの本教えて",
        "hook_hint": "「どんなジャンル好き？」「最近読んで良かった本ある？」"
    },
    {
        "user": "ゲームに飽きた",
        "hook_hint": "「どんなゲームやってた？」「新しいジャンル試す？」"
    },

    # 生活の悩み
    {
        "user": "部屋が片付かない",
        "hook_hint": "「何が一番散らかる？」「捨てられないタイプ？」"
    },
    {
        "user": "服のセンスがない",
        "hook_hint": "「どんな場面で着る服？」「好きな色は？」「予算は？」"
    },
    {
        "user": "引っ越ししたい",
        "hook_hint": "「どの辺に住みたい？」「今の家の不満は？」「予算は？」"
    },
    {
        "user": "一人暮らし始める",
        "hook_hint": "「初めて？」「何が一番不安？」「家具はこれから揃える？」"
    },

    # 季節・イベント
    {
        "user": "GWの予定がない",
        "hook_hint": "「遠出したい？近場でいい？」「一人？誰かと？」「予算は？」"
    },
    {
        "user": "クリスマス何する？",
        "hook_hint": "「誰と過ごす？」「予定ある？」「プレゼント選び困ってたりする？」"
    },
    {
        "user": "年末の大掃除めんどくさい",
        "hook_hint": "「どの部屋が一番ヤバい？」「いつからやる？」「完璧主義？」"
    },
    {
        "user": "夏バテ気味",
        "hook_hint": "「食欲ある？」「冷房効きすぎてない？」「水分ちゃんと取ってる？」"
    },

    # 技術・ガジェット
    {
        "user": "スマホ買い替えたい",
        "hook_hint": "「iPhone派？Android派？」「今の不満は？」「予算は？」"
    },
    {
        "user": "パソコン重い",
        "hook_hint": "「何年使ってる？」「メモリは？」「SSDに変えた？」"
    },
    {
        "user": "Wi-Fi遅い",
        "hook_hint": "「ルーター何年目？」「置き場所は？」「回線自体の問題かも？」"
    },

    # 深い話
    {
        "user": "将来が不安",
        "hook_hint": "「具体的に何が？」「仕事？健康？お金？」で整理を手伝う"
    },
    {
        "user": "自分に自信がない",
        "hook_hint": "共感後、「具体的にどんな場面で感じる？」「昔から？」"
    },
    {
        "user": "何のために生きてるか分からない",
        "hook_hint": "真摯に向き合いつつ、「最近何かあった？」「話聞くよ」"
    },
    {
        "user": "やりたいことが見つからない",
        "hook_hint": "「何をしてる時が楽しい？」「逆にやりたくないことは？」"
    },

    # ElioChat関連
    {
        "user": "AIって信用できる？",
        "hook_hint": "誠実に答えつつ、「何か心配なこと？」「どう使いたい？」"
    },
    {
        "user": "他のAIと何が違うの？",
        "hook_hint": "特徴を説明後、「どんな使い方したい？」"
    },
    {
        "user": "もっと賢くなれる？",
        "hook_hint": "謙虚に答えつつ、「足りないと思うこと？」「フィードバックあれば教えて」"
    },
    {
        "user": "ありがとう",
        "hook_hint": "感謝を受けつつ、「他に何か手伝えることある？」で会話を続ける選択肢を"
    },
]

async def generate_conversation_response(session: aiohttp.ClientSession, prompt: dict) -> dict | None:
    """会話継続応答を生成"""
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    messages = [
        {"role": "system", "content": CONVERSATION_SYSTEM},
        {"role": "user", "content": f"""以下の質問に対して、会話が続くような応答を生成してください。

質問: {prompt['user']}

フックのヒント: {prompt['hook_hint']}

回答形式:
1. <think>タグで思考過程を示す（ユーザーの意図、会話を続けるポイント）
2. 質問に対する適切な回答
3. 自然な流れで会話のフック（追加の質問や提案）を入れる
4. 押し付けがましくなく、選択肢を与える感じで"""}
    ]

    try:
        async with session.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-sonnet-4",
                "messages": messages,
                "max_tokens": 1500,
                "temperature": 0.7
            },
            ssl=ssl_context
        ) as response:
            if response.status == 200:
                data = await response.json()
                content = data["choices"][0]["message"]["content"]

                return {
                    "messages": [
                        {"role": "system", "content": CONVERSATION_SYSTEM},
                        {"role": "user", "content": prompt["user"]},
                        {"role": "assistant", "content": content}
                    ],
                    "metadata": {
                        "category": "conversation_hook",
                        "purpose": "retention"
                    }
                }
    except Exception as e:
        print(f"Error generating response: {e}")
    return None

async def main():
    print("会話継続データ生成開始...")

    connector = aiohttp.TCPConnector(limit=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = []

        for i, prompt in enumerate(CONVERSATION_PROMPTS):
            print(f"生成中: {i+1}/{len(CONVERSATION_PROMPTS)} - {prompt['user'][:20]}...")
            result = await generate_conversation_response(session, prompt)
            if result:
                results.append(result)
                print(f"  ✓ 完了")
            else:
                print(f"  ✗ 失敗")

            # Rate limiting
            await asyncio.sleep(1.5)

    # 保存
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n完了: {len(results)}件 -> {OUTPUT_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
