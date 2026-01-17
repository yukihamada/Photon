#!/usr/bin/env python3
"""
日本語思考データセット生成スクリプト

Qwen3-1.7Bを日本語thinkingに対応させるためのトレーニングデータを生成します。
"""

import json
import argparse
import random
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm


# 日本語思考データセットのテンプレート
# 様々なタスクタイプに対応

MATH_QUESTIONS = [
    {
        "question": "りんごが5個あります。3個食べたら残りは何個ですか？",
        "thinking": "まず、最初にあるりんごの数を確認しよう。5個ある。\n次に、食べた数を引く必要がある。3個食べた。\n計算: 5 - 3 = 2\nつまり、残りは2個だ。",
        "answer": "残りは2個です。"
    },
    {
        "question": "1から10までの数字を全部足すといくつになりますか？",
        "thinking": "1から10までの合計を求める問題だ。\n一つずつ足していく方法もあるが、等差数列の和の公式を使おう。\n公式: n(n+1)/2 で、n=10の場合\n10 × 11 / 2 = 110 / 2 = 55\n検算: 1+2+3+4+5+6+7+8+9+10 を順に足しても55になるはず。",
        "answer": "55になります。"
    },
    {
        "question": "3人で600円を均等に分けると、1人いくらですか？",
        "thinking": "均等に分けるということは、割り算をすればいい。\n600円 ÷ 3人 = 200円\nつまり、1人あたり200円になる。",
        "answer": "1人200円です。"
    },
    {
        "question": "時速60kmで2時間走ると、何km進みますか？",
        "thinking": "距離を求める問題だ。\n距離 = 速さ × 時間 の公式を使う。\n60km/h × 2h = 120km\nしたがって、120km進む。",
        "answer": "120km進みます。"
    },
    {
        "question": "2の5乗はいくつですか？",
        "thinking": "2の5乗とは、2を5回掛け合わせること。\n2^5 = 2 × 2 × 2 × 2 × 2\n= 4 × 2 × 2 × 2\n= 8 × 2 × 2\n= 16 × 2\n= 32",
        "answer": "32です。"
    },
]

LOGIC_QUESTIONS = [
    {
        "question": "全ての猫は動物です。タマは猫です。タマは動物ですか？",
        "thinking": "これは三段論法の問題だ。\n前提1: 全ての猫は動物である\n前提2: タマは猫である\n結論: よって、タマは動物である\nこれは論理的に正しい推論だ。",
        "answer": "はい、タマは動物です。"
    },
    {
        "question": "AはBより背が高い。BはCより背が高い。AとCではどちらが背が高いですか？",
        "thinking": "順序関係を整理しよう。\nA > B（AはBより高い）\nB > C（BはCより高い）\nこれを組み合わせると: A > B > C\nしたがって、AはCより背が高い。",
        "answer": "Aの方が背が高いです。"
    },
    {
        "question": "「雨が降れば地面が濡れる」が真のとき、「地面が濡れていない」場合、何が言えますか？",
        "thinking": "条件文の対偶を考える。\n元の命題: 雨が降る → 地面が濡れる\n対偶: 地面が濡れていない → 雨が降っていない\n対偶は元の命題と同値なので、「地面が濡れていない」なら「雨は降っていない」と言える。",
        "answer": "雨は降っていないと言えます。"
    },
    {
        "question": "5人の中から2人のリーダーを選ぶ方法は何通りありますか？",
        "thinking": "これは組み合わせの問題だ。順序は関係ない。\n5C2 = 5! / (2! × 3!)\n= (5 × 4) / (2 × 1)\n= 20 / 2\n= 10通り",
        "answer": "10通りあります。"
    },
]

CODING_QUESTIONS = [
    {
        "question": "Pythonでリストの要素を逆順にする方法を教えてください。",
        "thinking": "Pythonでリストを逆順にする方法はいくつかある。\n1. reverse()メソッド: 元のリストを変更する（破壊的）\n2. スライス [::-1]: 新しいリストを返す（非破壊的）\n3. reversed()関数: イテレータを返す\n最も簡潔なのはスライスを使う方法だろう。",
        "answer": "最も簡単な方法はスライスを使う方法です：\n```python\nmy_list = [1, 2, 3, 4, 5]\nreversed_list = my_list[::-1]  # [5, 4, 3, 2, 1]\n```\nまたは、元のリストを直接変更する場合は `my_list.reverse()` を使います。"
    },
    {
        "question": "再帰関数とは何ですか？",
        "thinking": "再帰関数について説明を求められている。\n再帰とは、関数が自分自身を呼び出すこと。\n重要な要素:\n1. 基底条件（base case）: 再帰を止める条件\n2. 再帰呼び出し: より小さな問題に分割\n例として階乗を挙げるとわかりやすい。",
        "answer": "再帰関数とは、関数の中で自分自身を呼び出す関数のことです。\n\n例（階乗の計算）:\n```python\ndef factorial(n):\n    if n <= 1:  # 基底条件\n        return 1\n    return n * factorial(n - 1)  # 再帰呼び出し\n```"
    },
    {
        "question": "リスト内包表記で1から10までの偶数のリストを作ってください。",
        "thinking": "リスト内包表記を使って偶数を抽出する。\n1から10までの範囲で、2で割り切れる数を選ぶ。\n条件: num % 2 == 0\nまたは、range(2, 11, 2)を使う方法もある。",
        "answer": "```python\neven_numbers = [num for num in range(1, 11) if num % 2 == 0]\n# 結果: [2, 4, 6, 8, 10]\n```\nまたは:\n```python\neven_numbers = list(range(2, 11, 2))\n```"
    },
]

GENERAL_QUESTIONS = [
    {
        "question": "なぜ空は青いのですか？",
        "thinking": "空が青い理由を科学的に説明する必要がある。\nこれはレイリー散乱という現象が関係している。\n太陽光は様々な波長の光を含んでいる。\n大気中の分子は短い波長（青色）の光をより多く散乱させる。\nそのため、空全体が青く見える。",
        "answer": "空が青く見えるのは「レイリー散乱」という現象のためです。太陽光が大気中の分子にぶつかると、青い光（短い波長）が他の色より多く散乱されます。この散乱した青い光が四方八方から目に届くため、空全体が青く見えるのです。"
    },
    {
        "question": "日本の首都はどこですか？",
        "thinking": "日本の首都についての質問だ。\n歴史的には京都が長く首都だったが、明治維新後に東京に遷都された。\n現在の日本の首都は東京である。",
        "answer": "日本の首都は東京です。"
    },
    {
        "question": "光合成とは何ですか？",
        "thinking": "光合成の説明を求められている。\n光合成は植物が行う重要な化学反応だ。\n必要なもの: 光、水、二酸化炭素\n生成物: 酸素、糖（グルコース）\n簡単に言うと、植物が光のエネルギーを使って食べ物を作る過程。",
        "answer": "光合成とは、植物が太陽の光エネルギーを使って、水と二酸化炭素からブドウ糖（栄養分）と酸素を作り出す反応です。植物の葉の葉緑体で行われ、地球上の酸素の主要な供給源となっています。"
    },
    {
        "question": "第二次世界大戦はいつ終わりましたか？",
        "thinking": "第二次世界大戦の終結時期について。\nヨーロッパ戦線: 1945年5月8日にドイツが降伏\nアジア太平洋戦線: 1945年8月15日に日本が降伏を発表\n正式な降伏文書への調印: 1945年9月2日\n一般的には1945年が終戦年とされる。",
        "answer": "第二次世界大戦は1945年に終わりました。ヨーロッパでは5月8日にドイツが降伏し、アジアでは8月15日に日本が降伏を発表しました。"
    },
]

CREATIVE_QUESTIONS = [
    {
        "question": "「月」をテーマに俳句を作ってください。",
        "thinking": "俳句を作る。五七五の形式で、月をテーマに。\n季語として「月」は秋の季語。\n情景を思い浮かべる...静かな夜、月明かり、影...\n「静けさ」と「月の光」を組み合わせてみよう。",
        "answer": "月明かり\n静かに照らす\n古い道\n\n（秋の夜、月の光が静かに古い道を照らしている情景を詠みました。）"
    },
    {
        "question": "短い怖い話を作ってください。",
        "thinking": "怖い話を短く作る。\n効果的な要素: 日常の中の異常、予想外の結末、読者の想像に委ねる部分\n設定: 一人暮らしの部屋で...\nオチを考える...鏡、影、足音などがよく使われる。",
        "answer": "一人暮らしを始めて3日目の夜。シャワーを浴びていると、曇った鏡に何か文字が浮かんでいた。「うしろ」。振り返ると誰もいない。安心してもう一度鏡を見ると、文字が増えていた。「まだいる」"
    },
]

CONVERSATION_QUESTIONS = [
    {
        "question": "最近疲れています。どうすればいいですか？",
        "thinking": "相談への回答。疲れている原因は様々ある。\n身体的疲労、精神的疲労、睡眠不足などが考えられる。\n一般的なアドバイスとして:\n1. 十分な睡眠\n2. 適度な運動\n3. 休息時間の確保\n4. ストレス解消\n共感を示しながら、実践的なアドバイスを。",
        "answer": "お疲れのことと思います。まずは十分な睡眠を取ることが大切です。また、軽い運動やストレッチ、好きなことをする時間を作るのも効果的です。疲れが長く続く場合は、無理せず医師に相談することもお勧めします。"
    },
    {
        "question": "友達と喧嘩してしまいました。仲直りしたいのですが...",
        "thinking": "人間関係の相談だ。\n仲直りしたいという気持ちは大切。\nアドバイスとして:\n1. まず冷静になる時間を置く\n2. 自分にも非がなかったか振り返る\n3. 素直に謝る\n4. 相手の話も聞く\n焦らずに、でも長く放置しすぎないことが重要。",
        "answer": "仲直りしたいという気持ちがあるのは素晴らしいことです。まずは少し時間を置いて、お互い冷静になってから話し合うのがいいでしょう。自分に非があった部分は素直に謝り、相手の気持ちもしっかり聞いてあげてください。長く放置せず、早めに連絡を取ることをお勧めします。"
    },
]


def create_sample(question: str, thinking: str, answer: str) -> Dict:
    """一つのトレーニングサンプルを作成"""
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f"<think>\n{thinking}\n</think>\n\n{answer}"}
        ]
    }


def generate_variations(base_questions: List[Dict], num_variations: int = 3) -> List[Dict]:
    """質問のバリエーションを生成（簡易版）"""
    variations = []
    for q in base_questions:
        variations.append(create_sample(q["question"], q["thinking"], q["answer"]))
    return variations


def generate_dataset(num_samples: int) -> List[Dict]:
    """データセット全体を生成"""
    all_questions = (
        MATH_QUESTIONS +
        LOGIC_QUESTIONS +
        CODING_QUESTIONS +
        GENERAL_QUESTIONS +
        CREATIVE_QUESTIONS +
        CONVERSATION_QUESTIONS
    )

    dataset = []

    # 基本的な質問を追加
    for q in all_questions:
        dataset.append(create_sample(q["question"], q["thinking"], q["answer"]))

    # 追加のサンプルが必要な場合はランダムに選択して追加
    while len(dataset) < num_samples:
        q = random.choice(all_questions)
        dataset.append(create_sample(q["question"], q["thinking"], q["answer"]))

    return dataset[:num_samples]


def save_dataset(dataset: List[Dict], output_path: str):
    """データセットをJSONL形式で保存"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"データセットを保存しました: {output_path}")
    print(f"サンプル数: {len(dataset)}")


def main():
    parser = argparse.ArgumentParser(description='日本語思考データセット生成')
    parser.add_argument('--output', type=str, default='data/japanese_thinking.jsonl',
                        help='出力ファイルパス')
    parser.add_argument('--num_samples', type=int, default=1000,
                        help='生成するサンプル数')
    args = parser.parse_args()

    print(f"日本語思考データセットを生成中... (目標: {args.num_samples}サンプル)")

    dataset = generate_dataset(args.num_samples)
    save_dataset(dataset, args.output)

    # サンプルを表示
    print("\n--- サンプルデータ ---")
    sample = random.choice(dataset)
    print(json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
