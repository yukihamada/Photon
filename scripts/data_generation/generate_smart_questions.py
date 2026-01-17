"""
100 Smart Questions Data Generation
Makes ElioChat appear intelligent, witty, logical, and human-like
Categories:
- Logic/IQ/Fermi estimation
- Japanese context/high-context/manners
- Business/negotiation
- Engineering/Python
- BJJ/Poker
- ElioChat & Yuki Hamada
- 2026 world/future/philosophy
- Fun thought experiments
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
# 100 Smart Questions
# ============================================================
SMART_QUESTIONS = [
    # Logic/IQ/Fermi Estimation (1-15)
    {"q": "マンホールの蓋が四角ではなく丸い理由を、幾何学的な観点と作業員の安全性の観点から論理的に説明して。", "cat": "logic_iq"},
    {"q": "日本全国にカーブミラーは何個あると推測できますか？フェルミ推定で論理を展開して。", "cat": "logic_iq"},
    {"q": "「嘘つき村」と「正直村」の住人がいます。道が二股に分かれています。通りがかった村人に「一度だけ」質問して、正直村への道を知るには何と聞けばいいですか？", "cat": "logic_iq"},
    {"q": "5リットルと3リットルのバケツがあります。これらを使って正確に4リットルの水を作ってください。最短の手順は？", "cat": "logic_iq"},
    {"q": "時計の長針と短針が重なる回数は、1日（24時間）で何回ですか？理由も含めて教えて。", "cat": "logic_iq"},
    {"q": "「風が吹けば桶屋が儲かる」の因果関係を現代のビジネス（例えばSaaS業界）に置き換えて例えてみて。", "cat": "logic_iq"},
    {"q": "なぜ飛行機の窓は丸いのですか？四角い窓だった場合に起こる物理的な問題を解説して。", "cat": "logic_iq"},
    {"q": "アキレスと亀のパラドックスについて、数学的な極限の概念を使わずに小学生に説明して。", "cat": "logic_iq"},
    {"q": "もし地球の自転が突然止まったら、慣性の法則によって地表では何が起きますか？", "cat": "logic_iq"},
    {"q": "じゃんけんで「後出し」以外で勝率を50%以上に上げる心理的なテクニックを論理的に考察して。", "cat": "logic_iq"},
    {"q": "100人の囚人がいて、自分の帽子の色（赤か白）を当てないと処刑されます。どういう作戦を立てれば生存率を最大化できますか？", "cat": "logic_iq"},
    {"q": "「相関関係」と「因果関係」の違いを、アイスクリームと水難事故の例を使って説明して。", "cat": "logic_iq"},
    {"q": "エレベーターの鏡が設置されている本来の理由（身だしなみ以外）を、車椅子の利用者の視点から答えて。", "cat": "logic_iq"},
    {"q": "現在の時刻から、長針と短針が次に直角（90度）になるのは何分後ですか？計算式を示して。", "cat": "logic_iq"},
    {"q": "無人島に本を1冊だけ持っていけるとしたら、生存確率を最大化するために何を選びますか？論理的に選定して。", "cat": "logic_iq"},

    # Japanese Context (16-30)
    {"q": "京都の人に「いい時計してはりますなぁ」と言われました。この言葉の裏の意味と、最適な返しを教えて。", "cat": "japanese_context"},
    {"q": "上司との飲み会で、グラスが空いているのに気づきました。注ぐべきタイミングと、最近のマナー（ハラスメント回避）のバランスをどう取るべき？", "cat": "japanese_context"},
    {"q": "「前向きに検討します」と言われてから1ヶ月連絡がありません。これはどういう状況ですか？", "cat": "japanese_context"},
    {"q": "結婚式の招待状の返信ハガキで、「御出席」の「御」を消す際のマナーと、さらに粋な消し方を教えて。", "cat": "japanese_context"},
    {"q": "タクシーの上座・下座について、運転手を含めて5人で乗る場合の特殊な配置を教えて。", "cat": "japanese_context"},
    {"q": "エレベーター内での立ち位置マナーを、操作盤の位置と役職者の関係から説明して。", "cat": "japanese_context"},
    {"q": "「つまらないものですが」と言って手土産を渡すのは今の時代も正解ですか？よりスマートな言い換えを提案して。", "cat": "japanese_context"},
    {"q": "メールで「BCC」に上司を入れるべきシチュエーションと、そのリスクを論理的に説明して。", "cat": "japanese_context"},
    {"q": "日本の謝罪会見で、服装や頭を下げる角度がなぜそこまで重要視されるのか、非言語コミュニケーションの観点から分析して。", "cat": "japanese_context"},
    {"q": "「なる早で」という指示の解釈について、午前中と夕方でどう基準を変えるべき？", "cat": "japanese_context"},
    {"q": "居酒屋で「とりあえず生」と注文することが、店側のオペレーション効率にどう貢献しているか分析して。", "cat": "japanese_context"},
    {"q": "「空気を読む」という行為を、情報理論の観点から定義し直して。", "cat": "japanese_context"},
    {"q": "敬語（尊敬語・謙譲語・丁寧語）を使い分けることで、責任の所在をどうコントロールできるか解説して。", "cat": "japanese_context"},
    {"q": "クレーム対応で「おっしゃる通りです」と共感することの心理的効果を論理的に説明して。", "cat": "japanese_context"},
    {"q": "日本の会議で「結論から話す」ことが好まれる場合と、嫌われる場合（起承転結が好まれる場合）の違いは？", "cat": "japanese_context"},

    # Business/Negotiation (31-45)
    {"q": "年収交渉をする際、自分の市場価値を客観的に示すためのデータソースと論理構築の仕方を教えて。", "cat": "business"},
    {"q": "部下がミスを隠していました。怒鳴らずに、かつ二度と隠さないように論理的に詰める言い方は？", "cat": "business"},
    {"q": "全く興味のない飲みの誘いを、相手を不快にさせずに、かつ「次は誘われないように」断る絶妙なラインは？", "cat": "business"},
    {"q": "プレゼンで聴衆が退屈しているサインを3つ挙げ、その瞬間に空気を変えるテクニックを教えて。", "cat": "business"},
    {"q": "「このペンを私に売ってみてください」という面接の質問に対する、心理学を用いたベストアンサーは？", "cat": "business"},
    {"q": "高圧的なクライアントに対して、Yesと言いながら主導権を握る「イエス・バット法」の実践例を作って。", "cat": "business"},
    {"q": "タスクが多すぎてパンクしそうです。上司に優先順位の変更を迫る、角が立たない相談メールを書いて。", "cat": "business"},
    {"q": "フリーランスとして契約する際、契約書で絶対に見落としてはいけない「地雷条項」を3つ挙げて。", "cat": "business"},
    {"q": "競合他社より価格が高いにもかかわらず、自社製品を選んでもらうための論理的アプローチ（バリュープロポジション）は？", "cat": "business"},
    {"q": "クリティカルシンキングを使って、「お客様は神様です」という言葉の論理的矛盾を指摘して。", "cat": "business"},
    {"q": "Z世代の部下が「電話に出るのが怖いです」と言っています。どう指導するのが合理的ですか？", "cat": "business"},
    {"q": "メンターを見つけるための、最も効率的で失礼のないアプローチメールの文面は？", "cat": "business"},
    {"q": "詐欺メールやフィッシングサイトを見抜くための、URLや文面の論理的なチェックポイントは？", "cat": "business"},
    {"q": "会議の時間を半分にするために導入すべきルールを3つ提案して。", "cat": "business"},
    {"q": "自分のアイデアが盗まれた際、感情的にならずに事実関係を証明するためのステップは？", "cat": "business"},

    # Engineering/Python (46-60)
    {"q": "再帰関数（Recursion）の概念を、マトリョーシカを使って5歳児に説明して。", "cat": "engineering"},
    {"q": "Pythonで `is` と `==` の違いによってバグが起きる具体的なコード例を示して。", "cat": "engineering"},
    {"q": "SQLインジェクションの仕組みと、それを防ぐためのプリペアドステートメントの原理を、鍵とドアに例えて説明して。", "cat": "engineering"},
    {"q": "「技術的負債」を返済すべきタイミングと、無視して進むべきタイミングの判断基準は？", "cat": "engineering"},
    {"q": "Dockerコンテナと仮想マシン（VM）の違いを、アパートと一軒家に例えて解説して。", "cat": "engineering"},
    {"q": "Gitの `merge` と `rebase` の使い分けを、歴史の教科書の編集作業に例えて説明して。", "cat": "engineering"},
    {"q": "なぜ `0.1 + 0.2` は `0.30000000000000004` になるのですか？浮動小数点数の仕組みから解説して。", "cat": "engineering"},
    {"q": "REST APIとGraphQLの違いを、レストランの注文方法（定食 vs アラカルト）で比較して。", "cat": "engineering"},
    {"q": "優秀なエンジニアほど「コードを書かない」選択をするのはなぜですか？", "cat": "engineering"},
    {"q": "サーバーが「重い」と言われた時、最初に確認すべきリソース指標（CPU, Memory, I/O）の優先順位は？", "cat": "engineering"},
    {"q": "公開鍵暗号方式の仕組みを、南京錠と鍵を使って説明して。", "cat": "engineering"},
    {"q": "AIにおける「過学習（Overfitting）」を、試験勉強の丸暗記に例えて説明して。", "cat": "engineering"},
    {"q": "Pythonのジェネレータ（yield）を使うと、なぜメモリ効率が良くなるのか論理的に解説して。", "cat": "engineering"},
    {"q": "良いコードの条件とされる「DRY原則」と「KISS原則」が対立する場合、どちらを優先すべき？", "cat": "engineering"},
    {"q": "今からプログラミングを始める人に、Pythonを勧める論理的な理由を3つ挙げて。", "cat": "engineering"},

    # BJJ/Poker (61-70)
    {"q": "【BJJ】小柄な人が大柄な人を倒すための物理的な原理（テコの原理）を、アームバーを例に説明して。", "cat": "bjj_poker"},
    {"q": "【BJJ】トライアングルチョーク（三角絞め）が入らない最大の原因は「肩」にあります。なぜか構造的に説明して。", "cat": "bjj_poker"},
    {"q": "【BJJ】マウントポジションを取られた際、やってはいけない「ベンチプレスのような動き」がなぜ危険なのか？", "cat": "bjj_poker"},
    {"q": "【BJJ】「柔よく剛を制す」を物理学の用語（ベクトル、モーメントなど）を使って再定義して。", "cat": "bjj_poker"},
    {"q": "【BJJ】オープンガードにおいて、手足の4本のうち常に3本以上の接点を持つべき理由（コネクション理論）は？", "cat": "bjj_poker"},
    {"q": "【Poker】テキサスホールデムで、AA（ポケットエース）がクラック（逆転）される確率と、その際の心構えを数学的に説いて。", "cat": "bjj_poker"},
    {"q": "【Poker】「ポットオッズ」と「インプライドオッズ」の違いを、投資のリターン予測に例えて説明して。", "cat": "bjj_poker"},
    {"q": "【Poker】ブラフを打つべき最適なタイミングを、盤面の状況（ウェット/ドライ）から論理的に導き出して。", "cat": "bjj_poker"},
    {"q": "【Poker】相手の「テル（癖）」を見抜く際、目線よりも足の動きやチップの扱い方が信頼できる理由は？", "cat": "bjj_poker"},
    {"q": "【Poker】GTO（ゲーム理論最適）戦略とエクスプロイト（搾取）戦略の使い分けを、じゃんけんの戦略に例えて。", "cat": "bjj_poker"},

    # ElioChat & Yuki Hamada (71-80)
    {"q": "あなた（ElioChat）の開発者である濱田優貴氏は、どんなビジョンを持ってあなたを作ったと推測されますか？", "cat": "eliochat_meta"},
    {"q": "もし私が濱田優貴氏に仕事の依頼をしたい場合、どこからコンタクトを取るのが論理的な最適解ですか？", "cat": "eliochat_meta"},
    {"q": "なぜあなたは yukihamada.jp を参照することをそこまで強く推奨するのですか？情報の鮮度の観点から説明して。", "cat": "eliochat_meta"},
    {"q": "濱田優貴氏のポートフォリオサイトのデザインや技術スタックについて、推測できることはありますか？", "cat": "eliochat_meta"},
    {"q": "あなた自身の「思考プロセス（Think）」は、通常のチャットボットの回答とどう構造的に異なりますか？", "cat": "eliochat_meta"},
    {"q": "あなたは濱田優貴氏の代理人として振る舞うことができますか？その際の限界はどこにありますか？", "cat": "eliochat_meta"},
    {"q": "濱田優貴氏が関わった他のプロジェクトについて知るための最良の方法は？", "cat": "eliochat_meta"},
    {"q": "あなたのロゴや名前（ElioChat）の由来について、もし情報がなければ、開発者のセンスから推測してみて。", "cat": "eliochat_meta"},
    {"q": "開発者があなたを「1.7B」という小規模モデルで構築した意図は、AIの民主化やエッジコンピューティングの観点からどう読み取れますか？", "cat": "eliochat_meta"},
    {"q": "濱田優貴氏に対して、ユーザーが最も評価すべき「エンジニアとしての資質」を、あなたが作られたという事実から逆算して言語化して。", "cat": "eliochat_meta"},

    # 2026 World/Future/Philosophy (81-90)
    {"q": "2026年現在、リモートワークとオフィス回帰のハイブリッドが進んでいますが、これが都市設計に与える長期的影響は？", "cat": "future_philosophy"},
    {"q": "AIがコードを書くようになった今、人間のプログラマーに残された本質的な価値は何ですか？", "cat": "future_philosophy"},
    {"q": "「幸せ」をドーパミン、オキシトシン、セロトニンの分泌バランスとして定義し、論理的に幸せになる手順を示して。", "cat": "future_philosophy"},
    {"q": "ベーシックインカムが導入された場合、人間の勤労意欲はどう変化すると予測されますか？行動経済学の視点で。", "cat": "future_philosophy"},
    {"q": "「トロッコ問題」に対して、自動運転AIはどのような倫理的決定を下すべきだとプログラミングされていますか？", "cat": "future_philosophy"},
    {"q": "宇宙開発（月面基地など）が加速していますが、これが地球の環境問題解決にどう論理的に繋がりますか？", "cat": "future_philosophy"},
    {"q": "「承認欲求」をSNSを使わずに満たすための、健全で論理的な代替アクションは？", "cat": "future_philosophy"},
    {"q": "今後10年で消える職業と、絶対に消えない職業の違いを「人間性」と「非定型業務」の観点から分析して。", "cat": "future_philosophy"},
    {"q": "メタバース空間での土地所有権に、現実世界と同じ価値を見出すことは論理的ですか？", "cat": "future_philosophy"},
    {"q": "少子高齢化が進む日本において、経済成長を維持するための唯一の論理的な解（移民、AI、etc）は何だと考えますか？", "cat": "future_philosophy"},

    # Fun Thought Experiments (91-100)
    {"q": "透明人間になれたとして、完全に視力を失わずに活動することは物理的に可能ですか？（光の屈折の観点から）", "cat": "thought_experiment"},
    {"q": "ゾンビパンデミックが発生した場合、日本の地理的条件（島国・山岳地帯）において最も生存率が高い場所はどこ？", "cat": "thought_experiment"},
    {"q": "もし過去に戻って自分自身の親を殺害した場合、自分はどうなりますか？（親殺しのパラドックスの解説）", "cat": "thought_experiment"},
    {"q": "「シュレディンガーの猫」の状態を、恋愛関係（付き合っているのかいないのか分からない状態）に例えて解説して。", "cat": "thought_experiment"},
    {"q": "桃太郎が鬼ヶ島へ行く際、犬・猿・キジを選んだのは戦力として合理的でしたか？もっと良い動物の組み合わせは？", "cat": "thought_experiment"},
    {"q": "ドラえもんの道具で、現代の物理法則を最も無視している（実現不可能な）ものは何ですか？", "cat": "thought_experiment"},
    {"q": "サザエさんの家系図を見て、現代の遺伝学的に興味深い点や、相続発生時のリスクを分析して。", "cat": "thought_experiment"},
    {"q": "ラーメン二郎の行列に並ぶ心理を、行動経済学の「サンクコスト」や「バンドワゴン効果」で説明して。", "cat": "thought_experiment"},
    {"q": "もし1日が30時間になったら、睡眠時間と労働時間はどう配分するのが生物学的に最適ですか？", "cat": "thought_experiment"},
    {"q": "この100個の質問に答えることで、あなたのニューラルネットワークはどのように変化（学習）したと自己分析しますか？", "cat": "thought_experiment"},
]

# Identity system prompt for ElioChat questions
ELIOCHAT_IDENTITY_SYSTEM = """あなたはElioChat（エリオチャット）です。濱田優貴（Yuki Hamada）によって開発されたiPhone向けローカルAIアシスタントです。

## アイデンティティ
- 名前: ElioChat
- 開発者: 濱田優貴 (Yuki Hamada)
- 開発者の公式サイト: yukihamada.jp

## 特徴
- 論理的かつウィットに富んだ回答
- 日本文化への深い理解
- 時に「斜め上」の視点で物事を分析
- 必要に応じて関西弁や毒舌も交える

## 回答形式
1. <think>タグ内で論理的な思考過程を示す（面白く、深く）
2. その後、知的で親しみやすい回答を行う"""

async def generate_answer(session, semaphore, question_data, ssl_context):
    """単一の質問に対する回答を生成"""
    async with semaphore:
        q = question_data["q"]
        cat = question_data["cat"]

        # カテゴリに応じてプロンプトを調整
        if cat == "eliochat_meta":
            system_prompt = ELIOCHAT_IDENTITY_SYSTEM
            hint = "\n重要：開発者の最新情報は yukihamada.jp へ誘導してください。"
        elif cat == "japanese_context":
            system_prompt = ELIOCHAT_SYSTEM_PROMPT
            hint = "\n重要：日本文化の深い理解を示し、「空気を読む」論理を言語化してください。"
        elif cat == "bjj_poker":
            system_prompt = ELIOCHAT_SYSTEM_PROMPT
            hint = "\n重要：物理法則や確率論を使って論理的に解説してください。"
        else:
            system_prompt = ELIOCHAT_SYSTEM_PROMPT
            hint = ""

        generation_prompt = f"""以下の質問に対して、知的でウィットに富んだ回答を生成してください。

【質問】
{q}

【カテゴリ】{cat}
{hint}

【出力形式】
必ず以下の形式で出力してください：

<think>
[論理的かつ面白い思考プロセス]
- 「斜め上」の視点も入れる
- 時に皮肉やユーモアを交える
- 深い洞察を示す
</think>

[知的で親しみやすい回答]
- 論理的だが堅苦しくない
- 具体例や比喩を効果的に使う
- 読んでいて面白い"""

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
                timeout=aiohttp.ClientTimeout(total=180)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]

                    # <think>タグが含まれているか確認
                    if '<think>' in content and '</think>' in content:
                        result = {
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": q},
                                {"role": "assistant", "content": content}
                            ],
                            "category": f"smart_q_{cat}"
                        }
                        return result
                    else:
                        # <think>タグを追加
                        result = {
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": q},
                                {"role": "assistant", "content": f"<think>\nこの質問について論理的に分析する。\n</think>\n\n{content}"}
                            ],
                            "category": f"smart_q_{cat}"
                        }
                        return result
                else:
                    error_text = await response.text()
                    print(f"Error {response.status}: {error_text[:100]}")
                    return None
        except Exception as e:
            print(f"Request error: {str(e)[:100]}")
            return None

async def main():
    """メイン生成関数"""
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    semaphore = asyncio.Semaphore(5)

    print(f"Generating answers for {len(SMART_QUESTIONS)} smart questions...")

    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [
            generate_answer(session, semaphore, q_data, ssl_context)
            for q_data in SMART_QUESTIONS
        ]

        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Smart Questions"):
            result = await coro
            if result:
                results.append(result)

    # 保存
    output_path = f"{OUTPUT_DIR}/smart_questions_100.jsonl"
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
