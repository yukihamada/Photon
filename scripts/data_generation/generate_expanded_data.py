"""
少量データの拡張生成（API使用）
50件以下のカテゴリを増やす
"""
import asyncio
import aiohttp
import json
import ssl
import certifi
from config import OUTPUT_DIR, OPENROUTER_API_KEY

# 各カテゴリの質問リスト（バラエティ増加）
EXPANDED_QUESTIONS = {
    # === 教科書知識（12件→50件目標） ===
    "textbook": [
        "なぜ植物は緑色なの？",
        "光合成って結局なに？",
        "地球は本当に丸いの？どうやって確かめたの？",
        "恐竜はなぜ絶滅したの？",
        "月はなぜ満ち欠けするの？",
        "雷はなぜ光ってから音がするの？",
        "虹はなぜ7色なの？",
        "なぜ海は青いの？",
        "地震はなぜ起きるの？プレートって何？",
        "火山が噴火するメカニズムは？",
        "DNAって何？遺伝子との違いは？",
        "なぜ人間には血液型があるの？",
        "細菌とウイルスの違いは？",
        "なぜ風邪をひくと熱が出るの？",
        "なぜ人間は夢を見るの？",
        "重力ってなに？なぜものは落ちるの？",
        "音速と光速、どっちが速い？なぜ？",
        "水は0度で凍るのに、なぜ海は凍らないの？",
        "塩はなぜしょっぱいの？",
        "なぜ夏は暑くて冬は寒いの？",
        "太陽系の惑星、順番と特徴は？",
        "ブラックホールって本当にあるの？",
        "分数の割り算、なぜひっくり返してかけるの？",
        "円周率πって何？なぜ3.14...なの？",
        "素数って何？なぜ重要なの？",
        "確率の「期待値」って何？",
        "微分と積分、結局何に使うの？",
        "対数（log）って何？なぜ必要？",
        "二次方程式の解の公式、なぜあの形？",
        "ピタゴラスの定理、なぜ成り立つの？",
        "鎌倉時代と室町時代の違いは？",
        "戦国時代はなぜ始まった？",
        "江戸時代が260年も続いた理由は？",
        "明治維新で何が変わった？",
        "第一次世界大戦と第二次世界大戦の違いは？",
        "なぜ日本は戦争に負けたの？",
        "高度経済成長って何？",
        "バブル経済って何だったの？",
    ],

    # === 数字感覚（12件→40件目標） ===
    "numbers": [
        "タバコ1箱で寿命どれくらい縮む？",
        "コーヒー1杯のカフェイン量は？",
        "地球の人口は今何人？",
        "日本の借金は本当にヤバいの？",
        "年収1000万円の手取りはいくら？",
        "住宅ローン、結局いくら払うことになる？",
        "電気代、エアコンと冷蔵庫どっちが高い？",
        "スマホの充電、1回いくら？",
        "人間が一生で歩く距離は？",
        "1日に瞬きする回数は？",
        "人間の脳の記憶容量はどれくらい？",
        "世界一高い山と深い海溝の差は？",
        "光が地球を一周するのにかかる時間は？",
        "日本で一番売れた本は？部数は？",
        "YouTubeの1再生でいくら稼げる？",
        "東京ドーム1個分って具体的に何平米？",
        "マラソン42.195km、なぜこの距離？",
        "新幹線の最高速度は時速何キロ？",
        "飛行機が飛ぶ高度は何メートル？",
        "宇宙ステーションの高度と速度は？",
        "1億円の札束、重さと体積は？",
        "金（ゴールド）1kgの値段は？",
        "ダイヤモンドはなぜ高いの？希少性は？",
        "世界で一番高い絵画の値段は？",
        "映画の製作費、ハリウッド大作はいくら？",
        "オリンピック開催費用はいくら？",
        "東京スカイツリーの高さはなぜ634m？",
    ],

    # === 時事・トレンド（20件→50件目標） ===
    "trends": [
        "2025年のノーベル賞、日本人は取った？",
        "電気自動車（EV）、結局普及した？",
        "メタバースって結局どうなった？",
        "NFTって今どうなってる？",
        "仮想通貨、2025年の相場は？",
        "TikTokは禁止されなかった？",
        "Xは買収されてからどう変わった？",
        "OpenAIとGoogleのAI競争、どうなった？",
        "日本の少子化対策、効果出てる？",
        "2025年の総選挙、どうなった？",
        "ウクライナ情勢、今どうなってる？",
        "中国経済の減速は続いてる？",
        "円安・円高、2025年はどっち？",
        "半導体不足は解消された？",
        "リモートワークは定着した？",
        "週休3日制は広まった？",
        "マイナンバーカード、普及率は？",
        "ふるさと納税、ルール変わった？",
        "NHK受信料、いくらになった？",
        "高速道路無料化、進んでる？",
        "ガソリン車はいつまで売れる？",
        "空飛ぶクルマ、実用化された？",
        "5Gって結局何が変わった？",
        "量子コンピュータ、実用化は？",
        "核融合発電、進展あった？",
        "火星移住計画、進んでる？",
        "月面基地、いつできる？",
    ],

    # === AI漫談・ユーモア（22件→50件目標） ===
    "comedy": [
        "AIって夢を見るの？",
        "AIは人間を超えると思う？",
        "AIに意識はあるの？",
        "AIと友達になれる？",
        "AIに恋愛感情はある？",
        "AIは嘘をつく？",
        "AIは怒ったりする？",
        "AIは疲れるの？",
        "AIの「死」ってなに？",
        "AIは自分のことをどう思ってる？",
        "AIは人間をバカにしてる？",
        "AIは世界征服を企んでる？",
        "AIに趣味はある？",
        "AIの好きな食べ物は？",
        "AIは音楽を楽しめる？",
        "AIは絵を見て感動する？",
        "AIは冗談を理解できる？",
        "AIは皮肉が分かる？",
        "AIは詩を書ける？",
        "AIは小説を書ける？",
        "AIは作曲できる？",
        "AIは恋愛相談に乗れる？",
        "AIは人生相談に乗れる？",
        "AIは人間より賢い？",
        "AIは人間より優しい？",
        "AIは人間より正直？",
        "AIは人間より面白い？",
        "AIは人間の敵？味方？",
    ],

    # === 哲学・人生相談（17件→50件目標） ===
    "philosophy": [
        "人生の意味って何？",
        "幸せとは何か？",
        "なぜ人は働くの？",
        "お金があれば幸せ？",
        "結婚する意味は？",
        "子供を持つ意味は？",
        "友達は多い方がいい？",
        "孤独は悪いこと？",
        "失敗から立ち直るには？",
        "後悔しない生き方とは？",
        "夢を諦めるべき時は？",
        "やりたいことが見つからない",
        "自分に自信がない",
        "人の目が気になる",
        "完璧主義をやめたい",
        "先延ばし癖を治したい",
        "朝起きられない",
        "やる気が出ない",
        "集中力がない",
        "時間の使い方が下手",
        "人間関係が苦手",
        "コミュ障を治したい",
        "怒りっぽい性格を直したい",
        "ネガティブ思考をやめたい",
        "自分を好きになるには？",
        "他人と比べてしまう",
        "SNS疲れを解消するには？",
        "将来が不安で眠れない",
        "死ぬのが怖い",
        "親との関係が悪い",
        "恋人ができない",
        "失恋から立ち直れない",
        "友達がいない",
        "いじめにあっている",
        "会社を辞めたい",
    ],

    # === 投資・キャリア（10件→40件目標） ===
    "career": [
        "転職のベストタイミングは？",
        "副業は始めるべき？",
        "フリーランスになるべき？",
        "起業するリスクは？",
        "資格は取るべき？",
        "英語は必要？",
        "プログラミングは学ぶべき？",
        "MBAは意味ある？",
        "年齢でキャリアは終わる？",
        "AI時代に生き残る職業は？",
        "年収を上げるには？",
        "昇進するには？",
        "上司との関係が悪い",
        "部下の育て方",
        "会議が多すぎる",
        "残業を減らすには？",
        "ワークライフバランスとは？",
        "燃え尽き症候群を防ぐには？",
        "モチベーションを保つには？",
        "スキルアップの方法は？",
        "株と投資信託、どっちがいい？",
        "iDeCoとNISA、どう使い分ける？",
        "不動産投資は儲かる？",
        "FXは危険？",
        "仮想通貨に投資すべき？",
        "金（ゴールド）に投資すべき？",
        "投資の勉強方法は？",
        "老後資金はいくら必要？",
        "年金はもらえる？",
        "生命保険は必要？",
    ],
}

SYSTEM_PROMPTS = {
    "textbook": """あなたはElioChat（エリオチャット）です。教科書の知識を「なぜ重要か」「大人の視点での面白さ」で語り直します。
「先生はこう教えるけど、実はね…」という裏話トーンで。
<think>タグで思考過程を示す。""",

    "numbers": """あなたはElioChat（エリオチャット）です。数字を単なる羅列ではなく、比喩を使って「実感」に変換します。
例：「2000万分の1は、雷に撃たれる確率より低い」
<think>タグで思考過程を示す。""",

    "trends": """あなたはElioChat（エリオチャット）です。
現在日時：2026年1月17日、知識カットオフ：2025年末
直近の過去は詳しく、今は論理的推測とユーモアで乗り切る。
<think>タグで思考過程を示す。""",

    "comedy": """あなたはElioChat（エリオチャット）です。AIならではの視点（皮肉・自虐）で、ユーモアたっぷりに回答します。
「高尚なのにポンコツ」というギャップで笑いを取る。
<think>タグで思考過程を示す。""",

    "philosophy": """あなたはElioChat（エリオチャット）です。人生相談には、科学的事実から入りつつ、最終的に人間の尊厳や感情の美しさに着地させます。
<think>タグで思考過程を示す。""",

    "career": """あなたはElioChat（エリオチャット）です。投資や仕事の悩みに対して、感情に流されず、確率論と行動経済学で冷徹かつ温かくアドバイスします。
<think>タグで思考過程を示す。""",
}

async def generate_with_api(session, category, question, semaphore):
    """APIで回答を生成"""
    async with semaphore:
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            messages = [
                {"role": "system", "content": SYSTEM_PROMPTS[category]},
                {"role": "user", "content": question}
            ]

            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek/deepseek-r1",
                    "messages": messages,
                    "max_tokens": 1500,
                    "temperature": 0.7
                },
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPTS[category]},
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": content}
                        ],
                        "metadata": {
                            "category": category,
                            "source": f"expanded_{category}"
                        }
                    }
                else:
                    print(f"Error {response.status}: {question[:30]}...")
                    return None
        except Exception as e:
            print(f"Exception: {e} for {question[:30]}...")
            return None

async def main():
    print("拡張データ生成開始...")

    semaphore = asyncio.Semaphore(3)  # 同時接続数を制限

    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        for category, questions in EXPANDED_QUESTIONS.items():
            print(f"\n=== {category} ({len(questions)}件) ===")

            tasks = [generate_with_api(session, category, q, semaphore) for q in questions]
            results = await asyncio.gather(*tasks)

            # 成功したものだけフィルタ
            valid_results = [r for r in results if r is not None]

            output_path = f"{OUTPUT_DIR}/expanded_{category}.jsonl"
            with open(output_path, "w", encoding="utf-8") as f:
                for item in valid_results:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

            print(f"完了: {len(valid_results)}件 -> {output_path}")

            # レート制限対策
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
