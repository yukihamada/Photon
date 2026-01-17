#!/usr/bin/env python3
"""
改善版 日本語思考データセット生成スクリプト v2

より詳細な計算過程と多様な問題を含む
"""

import json
import argparse
import random
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm


# べき乗計算（詳細なステップ）
POWER_QUESTIONS = [
    {
        "question": "2の10乗はいくつですか？",
        "thinking": """2の10乗を計算する。
2^1 = 2
2^2 = 2 × 2 = 4
2^3 = 4 × 2 = 8
2^4 = 8 × 2 = 16
2^5 = 16 × 2 = 32
2^6 = 32 × 2 = 64
2^7 = 64 × 2 = 128
2^8 = 128 × 2 = 256
2^9 = 256 × 2 = 512
2^10 = 512 × 2 = 1024
したがって、2の10乗は1024。""",
        "answer": "1024です。"
    },
    {
        "question": "2の8乗はいくつですか？",
        "thinking": """2の8乗を計算する。
2^1 = 2
2^2 = 4
2^3 = 8
2^4 = 16
2^5 = 32
2^6 = 64
2^7 = 128
2^8 = 256
したがって、2の8乗は256。""",
        "answer": "256です。"
    },
    {
        "question": "3の4乗はいくつですか？",
        "thinking": """3の4乗を計算する。
3^1 = 3
3^2 = 3 × 3 = 9
3^3 = 9 × 3 = 27
3^4 = 27 × 3 = 81
したがって、3の4乗は81。""",
        "answer": "81です。"
    },
    {
        "question": "5の3乗はいくつですか？",
        "thinking": """5の3乗を計算する。
5^1 = 5
5^2 = 5 × 5 = 25
5^3 = 25 × 5 = 125
したがって、5の3乗は125。""",
        "answer": "125です。"
    },
    {
        "question": "4の3乗はいくつですか？",
        "thinking": """4の3乗を計算する。
4^1 = 4
4^2 = 4 × 4 = 16
4^3 = 16 × 4 = 64
したがって、4の3乗は64。""",
        "answer": "64です。"
    },
    {
        "question": "2の5乗はいくつですか？",
        "thinking": """2の5乗を計算する。
2^1 = 2
2^2 = 2 × 2 = 4
2^3 = 4 × 2 = 8
2^4 = 8 × 2 = 16
2^5 = 16 × 2 = 32
したがって、2の5乗は32。""",
        "answer": "32です。"
    },
    {
        "question": "10の3乗はいくつですか？",
        "thinking": """10の3乗を計算する。
10^1 = 10
10^2 = 10 × 10 = 100
10^3 = 100 × 10 = 1000
したがって、10の3乗は1000。""",
        "answer": "1000です。"
    },
    {
        "question": "2の6乗はいくつですか？",
        "thinking": """2の6乗を計算する。
2^1 = 2
2^2 = 4
2^3 = 8
2^4 = 16
2^5 = 32
2^6 = 64
したがって、2の6乗は64。""",
        "answer": "64です。"
    },
    {
        "question": "2の7乗はいくつですか？",
        "thinking": """2の7乗を計算する。
2^1 = 2
2^2 = 4
2^3 = 8
2^4 = 16
2^5 = 32
2^6 = 64
2^7 = 128
したがって、2の7乗は128。""",
        "answer": "128です。"
    },
    {
        "question": "2の9乗はいくつですか？",
        "thinking": """2の9乗を計算する。
2^1 = 2
2^2 = 4
2^3 = 8
2^4 = 16
2^5 = 32
2^6 = 64
2^7 = 128
2^8 = 256
2^9 = 512
したがって、2の9乗は512。""",
        "answer": "512です。"
    },
]

# 四則演算（詳細なステップ）
ARITHMETIC_QUESTIONS = [
    {
        "question": "123 + 456 はいくつですか？",
        "thinking": """足し算を計算する。
一の位: 3 + 6 = 9
十の位: 2 + 5 = 7
百の位: 1 + 4 = 5
結果: 579""",
        "answer": "579です。"
    },
    {
        "question": "500 - 237 はいくつですか？",
        "thinking": """引き算を計算する。
500 - 237
= 500 - 200 - 37
= 300 - 37
= 263""",
        "answer": "263です。"
    },
    {
        "question": "25 × 4 はいくつですか？",
        "thinking": """掛け算を計算する。
25 × 4
= 25 × 2 × 2
= 50 × 2
= 100""",
        "answer": "100です。"
    },
    {
        "question": "144 ÷ 12 はいくつですか？",
        "thinking": """割り算を計算する。
144 ÷ 12
12 × 10 = 120
12 × 12 = 144
したがって、144 ÷ 12 = 12""",
        "answer": "12です。"
    },
    {
        "question": "15 × 15 はいくつですか？",
        "thinking": """15の2乗を計算する。
15 × 15
= (10 + 5) × 15
= 10 × 15 + 5 × 15
= 150 + 75
= 225""",
        "answer": "225です。"
    },
    {
        "question": "1000 ÷ 8 はいくつですか？",
        "thinking": """割り算を計算する。
1000 ÷ 8
= 1000 ÷ 2 ÷ 2 ÷ 2
= 500 ÷ 2 ÷ 2
= 250 ÷ 2
= 125""",
        "answer": "125です。"
    },
    {
        "question": "99 × 99 はいくつですか？",
        "thinking": """99の2乗を計算する。
99 × 99
= (100 - 1) × (100 - 1)
= 100 × 100 - 100 - 100 + 1
= 10000 - 200 + 1
= 9801""",
        "answer": "9801です。"
    },
    {
        "question": "7 × 8 × 9 はいくつですか？",
        "thinking": """順番に掛け算する。
7 × 8 = 56
56 × 9 = 504
したがって、7 × 8 × 9 = 504""",
        "answer": "504です。"
    },
]

# 文章題（詳細な推論）
WORD_PROBLEMS = [
    {
        "question": "りんごが10個あります。3個食べて、2個を友達にあげたら、残りは何個ですか？",
        "thinking": """順番に計算する。
最初のりんご: 10個
食べた後: 10 - 3 = 7個
友達にあげた後: 7 - 2 = 5個
残りは5個。""",
        "answer": "残りは5個です。"
    },
    {
        "question": "1から10までの数字を全部足すといくつになりますか？",
        "thinking": """1から10までの合計を求める。
方法1: 等差数列の和の公式
n(n+1)/2 で n=10
10 × 11 / 2 = 110 / 2 = 55

方法2: 順に足す
1+2=3, 3+3=6, 6+4=10, 10+5=15, 15+6=21, 21+7=28, 28+8=36, 36+9=45, 45+10=55

答えは55。""",
        "answer": "55になります。"
    },
    {
        "question": "時速60kmで2時間30分走ると、何km進みますか？",
        "thinking": """距離 = 速さ × 時間
2時間30分 = 2.5時間
60 km/h × 2.5 h = 150 km
したがって、150km進む。""",
        "answer": "150km進みます。"
    },
    {
        "question": "800円の商品を20%引きで買うと、いくらになりますか？",
        "thinking": """20%引きの計算。
割引額: 800 × 0.20 = 160円
支払額: 800 - 160 = 640円""",
        "answer": "640円になります。"
    },
    {
        "question": "3人で900円を均等に分けると、1人いくらですか？",
        "thinking": """均等に分ける = 割り算
900 ÷ 3 = 300
1人あたり300円。""",
        "answer": "1人300円です。"
    },
    {
        "question": "1個80円のりんごを5個と、1個120円のみかんを3個買いました。合計いくらですか？",
        "thinking": """それぞれの小計を計算して合計する。
りんご: 80 × 5 = 400円
みかん: 120 × 3 = 360円
合計: 400 + 360 = 760円""",
        "answer": "合計760円です。"
    },
]

# 論理問題（明確な推論）
LOGIC_QUESTIONS = [
    {
        "question": "AはBより背が高く、CはBより背が低いです。AとCではどちらが背が高いですか？",
        "thinking": """順序関係を整理する。
前提1: A > B（AはBより背が高い）
前提2: C < B（CはBより背が低い）
つまり: A > B > C
AとCを比較すると、Aの方が背が高い。""",
        "answer": "Aの方が背が高いです。"
    },
    {
        "question": "全ての猫は動物です。タマは猫です。タマは動物ですか？",
        "thinking": """三段論法で考える。
大前提: 全ての猫は動物である
小前提: タマは猫である
結論: タマは動物である
これは論理的に正しい推論。""",
        "answer": "はい、タマは動物です。"
    },
    {
        "question": "「雨が降れば地面が濡れる」が真のとき、「地面が乾いている」場合、何が言えますか？",
        "thinking": """対偶を使って考える。
元の命題: 雨が降る → 地面が濡れる
対偶: 地面が濡れていない → 雨が降っていない
「地面が乾いている」= 地面が濡れていない
したがって、雨は降っていない。""",
        "answer": "雨は降っていないと言えます。"
    },
    {
        "question": "月曜日の3日後は何曜日ですか？",
        "thinking": """曜日を順に数える。
月曜日の1日後: 火曜日
月曜日の2日後: 水曜日
月曜日の3日後: 木曜日""",
        "answer": "木曜日です。"
    },
    {
        "question": "5人の中から委員長と副委員長を選ぶ方法は何通りありますか？",
        "thinking": """順列の問題。委員長と副委員長は区別がある。
委員長の選び方: 5通り
副委員長の選び方: 残り4人から、4通り
合計: 5 × 4 = 20通り""",
        "answer": "20通りあります。"
    },
]

# 一般知識
GENERAL_QUESTIONS = [
    {
        "question": "日本の首都はどこですか？",
        "thinking": """日本の首都について。
明治維新後、東京（旧江戸）が首都となった。
現在の日本の首都は東京。""",
        "answer": "日本の首都は東京です。"
    },
    {
        "question": "日本で一番高い山は何ですか？",
        "thinking": """日本の最高峰について。
富士山は標高3776メートルで、日本一高い山。
静岡県と山梨県にまたがる。""",
        "answer": "富士山です。標高は3776メートルです。"
    },
    {
        "question": "水の化学式は何ですか？",
        "thinking": """水の分子構造を考える。
水は水素原子2つと酸素原子1つからなる。
化学式はH2O。""",
        "answer": "H2Oです。"
    },
    {
        "question": "1年は何日ですか？",
        "thinking": """1年の日数について。
通常の年: 365日
うるう年: 366日（4年に1度）
一般的には365日と答える。""",
        "answer": "通常は365日です。うるう年は366日になります。"
    },
    {
        "question": "太陽系で一番大きい惑星は何ですか？",
        "thinking": """太陽系の惑星のサイズを考える。
木星は太陽系最大の惑星。
直径は地球の約11倍。""",
        "answer": "木星です。"
    },
]

# コーディング問題
CODING_QUESTIONS = [
    {
        "question": "Pythonでリストを逆順にする方法を教えてください。",
        "thinking": """Pythonでリストを逆順にする方法は複数ある。
1. スライス: list[::-1] - 新しいリストを返す
2. reverse(): list.reverse() - 元のリストを変更
3. reversed(): list(reversed(list)) - イテレータを返す
最も簡潔なのはスライス。""",
        "answer": """最も簡単な方法はスライスを使う方法です：
```python
my_list = [1, 2, 3, 4, 5]
reversed_list = my_list[::-1]  # [5, 4, 3, 2, 1]
```"""
    },
    {
        "question": "Pythonで1から100までの偶数の合計を計算するコードを書いてください。",
        "thinking": """1から100までの偶数の合計。
方法1: forループ
方法2: リスト内包表記とsum
方法3: 数学的公式（等差数列の和）

リスト内包表記が簡潔。
偶数: 2, 4, 6, ..., 100
個数: 50個
合計: 2+4+6+...+100 = 2×(1+2+3+...+50) = 2×(50×51/2) = 2550""",
        "answer": """```python
# 方法1: sum とリスト内包表記
total = sum(i for i in range(2, 101, 2))  # 2550

# 方法2: 数学的計算
total = 50 * 51  # 2550
```
答えは2550です。"""
    },
    {
        "question": "Pythonで文字列が回文かどうか判定する関数を書いてください。",
        "thinking": """回文判定の関数。
回文とは、前から読んでも後ろから読んでも同じ文字列。
例: 「しんぶんし」「level」「radar」
文字列を逆順にして元と比較すればよい。""",
        "answer": """```python
def is_palindrome(s):
    # 大文字小文字を無視し、空白を除去
    s = s.lower().replace(' ', '')
    return s == s[::-1]

# 使用例
print(is_palindrome('level'))  # True
print(is_palindrome('hello'))  # False
```"""
    },
]

# 科学の説明
SCIENCE_QUESTIONS = [
    {
        "question": "なぜ空は青いのですか？",
        "thinking": """空が青い理由を科学的に説明する。
1. 太陽光は様々な波長の光を含む（虹の7色）
2. 大気中の分子は光を散乱させる（レイリー散乱）
3. 短い波長（青色）ほど散乱されやすい
4. 散乱された青い光が全方向から目に届く
5. そのため空全体が青く見える""",
        "answer": "空が青く見えるのは「レイリー散乱」という現象のためです。太陽光が大気中の分子にぶつかると、青い光（短い波長）が他の色より多く散乱されます。この散乱した青い光が四方八方から目に届くため、空全体が青く見えるのです。"
    },
    {
        "question": "なぜ夕焼けは赤いのですか？",
        "thinking": """夕焼けが赤い理由を説明する。
1. 夕方は太陽光が大気を通過する距離が長い
2. 青い光は途中で散乱されて届かなくなる
3. 赤い光は波長が長いので散乱されにくい
4. 残った赤い光が直接目に届く
5. そのため夕焼けは赤く見える""",
        "answer": "夕焼けが赤く見えるのは、夕方は太陽光が大気を長く通過するためです。青い光（短い波長）は途中で散乱されてしまい、波長が長く散乱されにくい赤い光だけが目に届きます。そのため夕焼けは赤く見えるのです。"
    },
    {
        "question": "光合成とは何ですか？",
        "thinking": """光合成について説明する。
1. 植物が行う化学反応
2. 必要なもの: 光、水(H2O)、二酸化炭素(CO2)
3. 生成物: ブドウ糖(C6H12O6)、酸素(O2)
4. 場所: 葉の葉緑体
5. 化学式: 6CO2 + 6H2O → C6H12O6 + 6O2""",
        "answer": "光合成とは、植物が太陽の光エネルギーを使って、水と二酸化炭素からブドウ糖（栄養分）と酸素を作り出す反応です。この反応は葉の葉緑体で行われ、地球上の酸素の主要な供給源となっています。"
    },
]


def create_sample(question: str, thinking: str, answer: str) -> Dict:
    """一つのトレーニングサンプルを作成"""
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f"<think>\n{thinking.strip()}\n</think>\n\n{answer}"}
        ]
    }


def generate_math_variations():
    """数学問題のバリエーションを動的に生成"""
    variations = []

    # べき乗のバリエーション
    for base in [2, 3, 4, 5]:
        for exp in range(2, 8):
            result = base ** exp
            steps = [f"{base}^1 = {base}"]
            current = base
            for i in range(2, exp + 1):
                current *= base
                steps.append(f"{base}^{i} = {current}")

            thinking = f"{base}の{exp}乗を計算する。\n" + "\n".join(steps) + f"\nしたがって、{base}の{exp}乗は{result}。"

            variations.append({
                "question": f"{base}の{exp}乗はいくつですか？",
                "thinking": thinking,
                "answer": f"{result}です。"
            })

    # 簡単な計算
    for _ in range(50):
        a = random.randint(10, 100)
        b = random.randint(10, 100)
        result = a + b
        variations.append({
            "question": f"{a} + {b} はいくつですか？",
            "thinking": f"足し算を計算する。\n{a} + {b} = {result}",
            "answer": f"{result}です。"
        })

        if a > b:
            result = a - b
            variations.append({
                "question": f"{a} - {b} はいくつですか？",
                "thinking": f"引き算を計算する。\n{a} - {b} = {result}",
                "answer": f"{result}です。"
            })

        a = random.randint(2, 20)
        b = random.randint(2, 20)
        result = a * b
        variations.append({
            "question": f"{a} × {b} はいくつですか？",
            "thinking": f"掛け算を計算する。\n{a} × {b} = {result}",
            "answer": f"{result}です。"
        })

    return variations


def generate_dataset(num_samples: int) -> List[Dict]:
    """データセット全体を生成"""
    all_questions = (
        POWER_QUESTIONS * 10 +  # べき乗を重点的に
        ARITHMETIC_QUESTIONS * 5 +
        WORD_PROBLEMS * 5 +
        LOGIC_QUESTIONS * 5 +
        GENERAL_QUESTIONS * 3 +
        CODING_QUESTIONS * 3 +
        SCIENCE_QUESTIONS * 3 +
        generate_math_variations()
    )

    dataset = []

    # 基本的な質問を追加
    for q in all_questions:
        dataset.append(create_sample(q["question"], q["thinking"], q["answer"]))

    # シャッフル
    random.shuffle(dataset)

    # 追加のサンプルが必要な場合
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
    parser = argparse.ArgumentParser(description='改善版 日本語思考データセット生成 v2')
    parser.add_argument('--output', type=str, default='data/japanese_thinking_v2.jsonl',
                        help='出力ファイルパス')
    parser.add_argument('--num_samples', type=int, default=50000,
                        help='生成するサンプル数')
    args = parser.parse_args()

    print(f"改善版データセットを生成中... (目標: {args.num_samples}サンプル)")

    dataset = generate_dataset(args.num_samples)
    save_dataset(dataset, args.output)

    # サンプルを表示
    print("\n--- サンプルデータ ---")
    for sample in random.sample(dataset, min(3, len(dataset))):
        print(json.dumps(sample, ensure_ascii=False, indent=2))
        print("---")


if __name__ == '__main__':
    main()
