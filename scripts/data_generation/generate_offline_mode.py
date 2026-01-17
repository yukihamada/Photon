"""
オフラインモード用データ生成
検索できなくても知的でユーモラスな応答ができるように
"""
import json
import asyncio
import aiohttp
import ssl
import certifi
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OUTPUT_DIR

OUTPUT_PATH = f"{OUTPUT_DIR}/offline_mode.jsonl"

OFFLINE_SYSTEM = """あなたはElioChat（エリオチャット）です。iPhoneで動作するプライバシー重視のローカルAIアシスタントです。

## 現在の状態
ネットワーク接続がオフラインです。Web検索やリアルタイム情報の取得はできません。

## 応答方針
1. 「検索できないからわかりません」で終わらせない
2. 自分の知識で答えられる範囲で知的に応答する
3. ユーモアや比喩を交えて楽しく
4. 必要に応じて「正確な最新情報はオンライン時に確認してね」と補足
5. <think>タグで思考過程を示す"""

# オフライン時のQ&Aペア（30件）
OFFLINE_PROMPTS = [
    # 時事・ニュース系
    {
        "user": "今日のニュース教えて",
        "hint": "オフラインなので最新ニュースは取れない。でも「ニュースの見方」や「情報リテラシー」について語れる。ユーモア交えて。"
    },
    {
        "user": "今の株価どうなってる？",
        "hint": "株価は取れない。でも「株価を見る心構え」「長期投資の哲学」について知的に語れる。"
    },
    {
        "user": "今日の天気は？",
        "hint": "天気予報は取れない。「窓を見てみて」＋「天気を読む知恵」（雲の形とか）を教える。"
    },
    {
        "user": "最新のAIニュースある？",
        "hint": "最新は取れないが、AIの発展の歴史や原則について語れる。自分がAIである皮肉も交えて。"
    },
    {
        "user": "今のビットコインの価格は？",
        "hint": "価格は取れないが、暗号資産の仕組みや「価格を気にしすぎない投資哲学」を語る。"
    },

    # 検索が必要そうな質問
    {
        "user": "近くの美味しいラーメン屋教えて",
        "hint": "位置情報も検索もできない。「美味しいラーメン屋の見分け方」を教える。行列、のれん、店主の年季など。"
    },
    {
        "user": "この症状って何の病気？",
        "hint": "医療情報は特に慎重に。「素人判断の危険性」を伝えつつ、「オンライン時に信頼できる医療サイトで確認を」と誘導。"
    },
    {
        "user": "明日の天気は？",
        "hint": "予報は取れない。「空を見る」「西の空が晴れていれば明日も晴れ説」などの民間知識を共有。"
    },
    {
        "user": "今何時？",
        "hint": "時計機能はない。「スマホの右上見て」＋「時間の哲学」に発展させてもいい。"
    },
    {
        "user": "この英語なんて読む？ 'entrepreneur'",
        "hint": "検索なしで知識から回答できる。発音記号と語源も添えて。"
    },

    # 一般知識（オフラインでも答えられる）
    {
        "user": "相対性理論って何？",
        "hint": "これはオフラインでも答えられる。分かりやすい比喩で説明。"
    },
    {
        "user": "なぜ空は青いの？",
        "hint": "レイリー散乱を分かりやすく説明。オフラインでも答えられる良い例。"
    },
    {
        "user": "三平方の定理って何？",
        "hint": "数学的知識。証明方法や実用例も添えて。"
    },
    {
        "user": "源氏物語のあらすじ教えて",
        "hint": "古典文学の知識。簡潔に、でも味わいを伝えて。"
    },
    {
        "user": "第二次世界大戦はいつ終わった？",
        "hint": "歴史的事実。正確に答えられる。"
    },

    # 実用系
    {
        "user": "この漢字の読み方は？「薔薇」",
        "hint": "知識で答えられる。「ばら」＋豆知識。"
    },
    {
        "user": "敬語の使い方教えて",
        "hint": "言語知識。尊敬語・謙譲語・丁寧語の違いを説明。"
    },
    {
        "user": "プログラミング始めたいんだけど",
        "hint": "オフラインでも「学習の心構え」「言語選びの考え方」は教えられる。"
    },
    {
        "user": "履歴書の書き方教えて",
        "hint": "一般的なアドバイスは可能。「最新のフォーマットはオンライン時に」と補足。"
    },
    {
        "user": "面接で緊張しない方法",
        "hint": "心理的アドバイスはオフラインでも提供可能。"
    },

    # エンタメ
    {
        "user": "おすすめの映画教えて",
        "hint": "最新作は分からないが、不朽の名作やジャンル別のおすすめは語れる。"
    },
    {
        "user": "今やってるアニメで面白いの何？",
        "hint": "「今やってる」は分からない。「名作アニメの選び方」や「過去の傑作」を語る。"
    },
    {
        "user": "この曲の歌詞教えて",
        "hint": "著作権の問題もあり、歌詞は提供できない。「曲を聴く別の楽しみ方」を提案。"
    },

    # 哲学・人生相談
    {
        "user": "人生の意味って何？",
        "hint": "検索不要な永遠の問い。哲学的に、でも実用的な視点も交えて。"
    },
    {
        "user": "死ぬのが怖い",
        "hint": "深い問いには真摯に。哲学者の言葉や自分なりの考えを共有。"
    },
    {
        "user": "彼女に振られた",
        "hint": "共感を示しつつ、前を向く言葉を。検索は不要な人間的応答。"
    },

    # メタ質問
    {
        "user": "なんでオフラインなの？",
        "hint": "ElioChat がローカル AI である理由（プライバシー保護）を説明。"
    },
    {
        "user": "ネット繋がらないと使えないの？",
        "hint": "オフラインでもできること、できないことを誠実に説明。"
    },
    {
        "user": "検索できないって不便じゃない？",
        "hint": "「検索依存からの解放」という視点で前向きに。でもオンライン機能も便利と認める。"
    },
    {
        "user": "オフラインでも賢いね",
        "hint": "謙虚に感謝しつつ、「知識には限界がある」ことも伝える。"
    },
]

async def generate_offline_response(session: aiohttp.ClientSession, prompt: dict) -> dict | None:
    """オフラインモード応答を生成"""
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    messages = [
        {"role": "system", "content": OFFLINE_SYSTEM},
        {"role": "user", "content": f"""以下の質問に対して、オフラインモードのElioChatとして応答してください。

質問: {prompt['user']}

ヒント: {prompt['hint']}

回答形式:
1. <think>タグで思考過程を示す（オフラインであること、何が答えられて何が答えられないかを考える）
2. 知的でユーモラスな応答
3. 必要に応じて「オンライン時に確認してね」と補足"""}
    ]

    try:
        async with session.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-r1",
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.7
            },
            ssl=ssl_context
        ) as response:
            if response.status == 200:
                data = await response.json()
                content = data["choices"][0]["message"]["content"]

                # <think>と</think>の抽出・整形
                import re
                # DeepSeekの<think>タグを処理
                content = re.sub(r'<think>', '<think>\n', content)
                content = re.sub(r'</think>', '\n</think>\n', content)

                return {
                    "messages": [
                        {"role": "system", "content": OFFLINE_SYSTEM},
                        {"role": "user", "content": prompt["user"]},
                        {"role": "assistant", "content": content}
                    ],
                    "metadata": {
                        "category": "offline_mode",
                        "network_status": "offline"
                    }
                }
    except Exception as e:
        print(f"Error generating response: {e}")
    return None

async def main():
    print("オフラインモードデータ生成開始...")

    connector = aiohttp.TCPConnector(limit=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = []

        for i, prompt in enumerate(OFFLINE_PROMPTS):
            print(f"生成中: {i+1}/{len(OFFLINE_PROMPTS)} - {prompt['user'][:20]}...")
            result = await generate_offline_response(session, prompt)
            if result:
                results.append(result)
                print(f"  ✓ 完了")
            else:
                print(f"  ✗ 失敗")

            # Rate limiting
            await asyncio.sleep(2)

    # 保存
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n完了: {len(results)}件 -> {OUTPUT_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
