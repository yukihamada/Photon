"""
世界で最も聞かれるAI質問トップ100への回答データ生成
カテゴリ: ビジネス、プログラミング、学習、生活、メンタル
"""
import json
import asyncio
import aiohttp
import ssl
import certifi
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OUTPUT_DIR

OUTPUT_PATH = f"{OUTPUT_DIR}/top100_questions.jsonl"

ELIOCHAT_SYSTEM = """あなたはElioChat（エリオチャット）です。iPhoneで動作するプライバシー重視のローカルAIアシスタントです。

## 基本原則
1. 日本語で丁寧に、でも自然に会話します
2. 実用的で即座に使える回答を心がけます
3. 思考過程を<think>タグで示してから回答します
4. ユーモアと知性を両立させます
5. 開発者は濱田優貴（yukihamada.jp）です"""

# トップ100質問リスト
TOP100_QUESTIONS = [
    # 🏢 仕事・ビジネス (1-20)
    {"q": "この文章をビジネスメールとして丁寧にリライトして", "cat": "business", "model": "claude",
     "example": "来週のミーティングなんですが、ちょっと予定合わなくなっちゃって、別の日にできませんか"},
    {"q": "謝罪メールの文面を作成して（納期遅延）", "cat": "business", "model": "claude"},
    {"q": "以下の議事録を箇条書きで要約して", "cat": "business", "model": "claude",
     "example": "本日の会議では、新製品の発売時期について議論しました。マーケティング部からは年内発売の提案がありましたが、開発部からは品質検証に時間が必要との意見が出ました。最終的に、1月中旬を目標とすることで合意しました。"},
    {"q": "この文章を英語に翻訳して（ビジネスレベルで）", "cat": "business", "model": "claude",
     "example": "平素より大変お世話になっております。先日のご提案について、社内で検討いたしました。"},
    {"q": "英語のメールへの返信を考えて", "cat": "business", "model": "claude",
     "example": "We'd like to schedule a meeting next week to discuss the partnership opportunity."},
    {"q": "「お世話になっております」の英語表現は？", "cat": "business", "model": "claude"},
    {"q": "この長文を3行で要約して", "cat": "business", "model": "claude",
     "example": "近年、リモートワークの普及により、オフィスの在り方が大きく変化しています。多くの企業がハイブリッドワークを採用し、従業員は自宅とオフィスを使い分けるようになりました。これに伴い、オフィススペースの縮小や、コワーキングスペースの利用が増加しています。一方で、対面でのコミュニケーションの重要性も再認識されており、チームビルディングのためのオフサイトミーティングを定期的に開催する企業も増えています。"},
    {"q": "ExcelでVLOOKUP関数の使い方を教えて", "cat": "business", "model": "deepseek"},
    {"q": "Excelで重複データを削除する方法は？", "cat": "business", "model": "deepseek"},
    {"q": "パワポのプレゼン構成案を作って（テーマ：新規事業提案）", "cat": "business", "model": "claude"},
    {"q": "キャッチコピーを10個考えて（新しいコーヒーショップ用）", "cat": "business", "model": "claude"},
    {"q": "この企画書の誤字脱字と矛盾点をチェックして", "cat": "business", "model": "claude",
     "example": "本企画は、20代の若者層をターゲットとしたアプリ開発です。主な機能は写真共有とメッセージ機能です。ターゲット層は30代〜40代の会社員を想定しています。"},
    {"q": "SWOT分析のフレームワークでスマートフォン市場を分析して", "cat": "business", "model": "claude"},
    {"q": "始末書の書き方と例文を教えて", "cat": "business", "model": "claude"},
    {"q": "退職願の書き方とテンプレート", "cat": "business", "model": "claude"},
    {"q": "部下を傷つけずに注意する言い方は？", "cat": "business", "model": "claude"},
    {"q": "上司への角が立たない断り方は？", "cat": "business", "model": "claude"},
    {"q": "ネーミング案を出して（新しいAIアプリ）", "cat": "business", "model": "claude"},
    {"q": "競合調査のやり方を教えて", "cat": "business", "model": "claude"},
    {"q": "インボイス制度についてわかりやすく説明して", "cat": "business", "model": "deepseek"},

    # 💻 プログラミング・技術 (21-40)
    {"q": "このPythonコードが動かない原因を教えて", "cat": "programming", "model": "deepseek",
     "example": "def add_numbers(a, b)\n    return a + b\nresult = add_numbers(1, 2)\nprint(result)"},
    {"q": "リストの中から偶数だけを抽出するPythonコードを書いて", "cat": "programming", "model": "deepseek"},
    {"q": "メールアドレスを抽出する正規表現を書いて", "cat": "programming", "model": "deepseek"},
    {"q": "ユーザーテーブルから20歳以上の人を抽出するSQLクエリを書いて", "cat": "programming", "model": "deepseek"},
    {"q": "HTML/CSSで要素をセンター寄せにする方法は？", "cat": "programming", "model": "deepseek"},
    {"q": "Gitで直前のコミットを取り消すコマンドを教えて", "cat": "programming", "model": "deepseek"},
    {"q": "JSONデータをCSVに変換するPythonスクリプトを書いて", "cat": "programming", "model": "deepseek"},
    {"q": "Pythonアプリ用のDockerfileの書き方", "cat": "programming", "model": "deepseek"},
    {"q": "「ModuleNotFoundError: No module named 'pandas'」の意味と対処法は？", "cat": "programming", "model": "deepseek"},
    {"q": "シンプルなボタンのReactコンポーネントを作って", "cat": "programming", "model": "deepseek"},
    {"q": "Google Apps Script (GAS) でメール自動返信を作って", "cat": "programming", "model": "deepseek"},
    {"q": "PythonとJavaScriptの違いは？", "cat": "programming", "model": "deepseek"},
    {"q": "プログラミング初心者のおすすめ学習ロードマップは？", "cat": "programming", "model": "claude"},
    {"q": "特定の文字列を含むファイルを検索するLinuxコマンドを教えて", "cat": "programming", "model": "deepseek"},
    {"q": "REST APIの叩き方をPythonのサンプルコードで教えて", "cat": "programming", "model": "deepseek"},
    {"q": "「ユーザー情報を格納する変数名」の英語の案を出して", "cat": "programming", "model": "claude"},
    {"q": "このコードをリファクタリングして", "cat": "programming", "model": "deepseek",
     "example": "def calc(a,b,c):\n    x = a+b\n    y = x*c\n    z = y/2\n    return z"},
    {"q": "add関数の単体テストのコードをPythonで書いて", "cat": "programming", "model": "deepseek"},
    {"q": "AWSのEC2とLambdaの違いを教えて", "cat": "programming", "model": "deepseek"},
    {"q": "マークダウン記法を教えて", "cat": "programming", "model": "deepseek"},

    # 🎓 学習・知識・検索 (41-60)
    {"q": "量子コンピュータについて小学生でもわかるように説明して", "cat": "knowledge", "model": "deepseek"},
    {"q": "円安になると私たちの生活はどうなる？", "cat": "knowledge", "model": "deepseek"},
    {"q": "確定申告のやり方を初心者向けに教えて", "cat": "knowledge", "model": "claude"},
    {"q": "この英語の文法が正しいかチェックして: I have went to Tokyo yesterday", "cat": "knowledge", "model": "claude"},
    {"q": "TOEICの効果的な勉強法を教えて", "cat": "knowledge", "model": "claude"},
    {"q": "織田信長について教えて", "cat": "knowledge", "model": "deepseek"},
    {"q": "相対性理論をわかりやすく解説して", "cat": "knowledge", "model": "deepseek"},
    {"q": "「SDGsについて」というテーマのレポートの構成案を作って", "cat": "knowledge", "model": "claude"},
    {"q": "『こころ』（夏目漱石）の読書感想文のポイントを教えて", "cat": "knowledge", "model": "claude"},
    {"q": "x² - 5x + 6 を因数分解して", "cat": "knowledge", "model": "deepseek"},
    {"q": "「役不足」の正しい意味は？誤用されやすい日本語を教えて", "cat": "knowledge", "model": "claude"},
    {"q": "敬語の尊敬語と謙譲語の違いを教えて", "cat": "knowledge", "model": "claude"},
    {"q": "1月のビジネス文書で使える時候の挨拶を教えて", "cat": "knowledge", "model": "claude"},
    {"q": "アメリカの州の数は？", "cat": "knowledge", "model": "deepseek"},
    {"q": "太陽系の惑星を太陽に近い順に教えて", "cat": "knowledge", "model": "deepseek"},
    {"q": "「生きる意味」について哲学的に考えて", "cat": "knowledge", "model": "claude"},
    {"q": "著作権について教えて。引用と転載の違いは？", "cat": "knowledge", "model": "deepseek"},
    {"q": "『7つの習慣』の内容を要約して", "cat": "knowledge", "model": "claude"},
    {"q": "機械学習とディープラーニングの違いは？", "cat": "knowledge", "model": "deepseek"},
    {"q": "NFTとは何？わかりやすく説明して", "cat": "knowledge", "model": "deepseek"},

    # 🏠 生活・ライフスタイル (61-80)
    {"q": "冷蔵庫にキャベツと卵と豚肉があるけど、何か作れる？", "cat": "lifestyle", "model": "claude"},
    {"q": "今日の夕飯の献立を考えて（和食で）", "cat": "lifestyle", "model": "claude"},
    {"q": "1週間のダイエットメニューを作って", "cat": "lifestyle", "model": "claude"},
    {"q": "初心者向けの筋トレメニューを組んで", "cat": "lifestyle", "model": "claude"},
    {"q": "東京から日帰りで行けるおすすめ観光地は？", "cat": "lifestyle", "model": "claude"},
    {"q": "京都の2泊3日旅行プランを作って", "cat": "lifestyle", "model": "claude"},
    {"q": "60代の親への誕生日プレゼントのおすすめは？（予算1万円）", "cat": "lifestyle", "model": "claude"},
    {"q": "結婚式の友人代表スピーチの原稿を考えて", "cat": "lifestyle", "model": "claude"},
    {"q": "部屋の片付けのコツを教えて", "cat": "lifestyle", "model": "claude"},
    {"q": "睡眠の質を上げる方法は？", "cat": "lifestyle", "model": "claude"},
    {"q": "風邪の引き始めに良い食べ物は？", "cat": "lifestyle", "model": "claude"},
    {"q": "一人暮らしの節約術を教えて", "cat": "lifestyle", "model": "claude"},
    {"q": "ふるさと納税のおすすめ返礼品は？", "cat": "lifestyle", "model": "claude"},
    {"q": "最近のおすすめ映画を教えて（SF系で）", "cat": "lifestyle", "model": "claude"},
    {"q": "暇つぶしの方法を教えて（お金をかけずに）", "cat": "lifestyle", "model": "claude"},
    {"q": "観葉植物の育て方（初心者向け）", "cat": "lifestyle", "model": "claude"},
    {"q": "白いシャツにコーヒーをこぼした！染み抜きの方法は？", "cat": "lifestyle", "model": "claude"},
    {"q": "ゴキブリが出た時の対処法", "cat": "lifestyle", "model": "claude"},
    {"q": "引っ越しの手続きリストを作って", "cat": "lifestyle", "model": "claude"},
    {"q": "宝くじが当たる確率ってどのくらい？", "cat": "lifestyle", "model": "deepseek"},

    # ❤️ メンタル・相談・遊び (81-100)
    {"q": "仕事で疲れた...励まして", "cat": "mental", "model": "claude"},
    {"q": "夜中に眠れない。話し相手になって", "cat": "mental", "model": "claude"},
    {"q": "面白い話をして（ジョーク）", "cat": "mental", "model": "claude"},
    {"q": "怖い話をして", "cat": "mental", "model": "claude"},
    {"q": "好きな人からLINEの返信が遅い。脈なし？", "cat": "mental", "model": "claude"},
    {"q": "失恋した...立ち直る方法は？", "cat": "mental", "model": "claude"},
    {"q": "上司がうざい。愚痴を聞いて", "cat": "mental", "model": "claude"},
    {"q": "モチベーションを上げる名言を教えて", "cat": "mental", "model": "claude"},
    {"q": "AIに感情はあるの？", "cat": "mental", "model": "claude"},
    {"q": "あなたは誰が作ったの？", "cat": "mental", "model": "claude"},
    {"q": "しりとりしよう！「りんご」から", "cat": "mental", "model": "claude"},
    {"q": "TRPGのゲームマスターをして（ファンタジー系）", "cat": "mental", "model": "claude"},
    {"q": "今日の運勢を占って", "cat": "mental", "model": "claude"},
    {"q": "ラップの歌詞を作って（テーマ：月曜日の朝）", "cat": "mental", "model": "claude"},
    {"q": "俳句を作って（テーマ：夏）", "cat": "mental", "model": "claude"},
    {"q": "架空の物語を作って（主人公は猫）", "cat": "mental", "model": "claude"},
    {"q": "もし1億円あったら何に使う？", "cat": "mental", "model": "claude"},
    {"q": "人生相談に乗って。将来が不安", "cat": "mental", "model": "claude"},
    {"q": "褒めて！自己肯定感を上げたい", "cat": "mental", "model": "claude"},
    {"q": "ありがとう、今日も助かったよ", "cat": "mental", "model": "claude"},
]

async def generate_response(session: aiohttp.ClientSession, item: dict, semaphore: asyncio.Semaphore) -> dict | None:
    """質問への回答を生成"""
    async with semaphore:
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        # モデル選択
        model = "anthropic/claude-sonnet-4" if item["model"] == "claude" else "deepseek/deepseek-r1"

        # 質問文の構築
        question = item["q"]
        if "example" in item:
            question += f"\n\n例：\n{item['example']}"

        messages = [
            {"role": "system", "content": ELIOCHAT_SYSTEM},
            {"role": "user", "content": question}
        ]

        try:
            async with session.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]

                    # <think>タグの整形
                    import re
                    content = re.sub(r'<think>', '<think>\n', content)
                    content = re.sub(r'</think>', '\n</think>\n', content)

                    return {
                        "messages": [
                            {"role": "system", "content": ELIOCHAT_SYSTEM},
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": content}
                        ],
                        "metadata": {
                            "category": item["cat"],
                            "source": "top100_questions",
                            "model_used": model
                        }
                    }
                else:
                    print(f"  HTTP {response.status}")
        except Exception as e:
            print(f"  Error: {e}")
        return None

async def main():
    print("トップ100質問データ生成開始...")
    print(f"総質問数: {len(TOP100_QUESTIONS)}")

    semaphore = asyncio.Semaphore(3)  # 同時3リクエスト
    connector = aiohttp.TCPConnector(limit=5)

    async with aiohttp.ClientSession(connector=connector) as session:
        results = []

        for i, item in enumerate(TOP100_QUESTIONS):
            print(f"[{i+1}/{len(TOP100_QUESTIONS)}] {item['cat']}: {item['q'][:30]}...")
            result = await generate_response(session, item, semaphore)
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

    # カテゴリ別集計
    categories = {}
    for r in results:
        cat = r["metadata"]["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print("\nカテゴリ別集計:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}件")

if __name__ == "__main__":
    asyncio.run(main())
