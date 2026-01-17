"""
Generate math/logic training data using templates (no API needed)
Focus on: power calculations, arithmetic, sequences, basic algebra
"""
import json
import random
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import sys
sys.path.append(str(Path(__file__).parent))
from config import ELIOCHAT_SYSTEM_PROMPT, OUTPUT_DIR


def calculate_power(base: int, exp: int) -> tuple:
    """Calculate power with step-by-step explanation"""
    result = 1
    steps = []
    for i in range(1, exp + 1):
        result *= base
        steps.append(f"{base}^{i} = {result}")
    return result, steps


def generate_power_examples(count: int = 1000) -> List[Dict]:
    """Generate power calculation examples"""
    examples = []
    bases = [2, 3, 5, 10]

    for _ in range(count):
        base = random.choice(bases)
        exp = random.randint(2, 12 if base == 2 else 6)
        result, steps = calculate_power(base, exp)

        # Question variations
        questions = [
            f"{base}の{exp}乗を計算してください。",
            f"{base}^{exp}はいくつですか？",
            f"{base}の{exp}乗は？",
            f"{base}を{exp}回かけるといくつになりますか？",
        ]
        question = random.choice(questions)

        # Thinking process
        thinking = f"{base}の{exp}乗を計算する。\n順番に計算していく。\n"
        thinking += "\n".join(steps[-min(5, len(steps)):])  # Show last 5 steps

        response = f"<think>\n{thinking}\n</think>\n\n{base}の{exp}乗は **{result}** です。"

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": response}
            ]
        })

    return examples


def generate_arithmetic_examples(count: int = 1000) -> List[Dict]:
    """Generate arithmetic calculation examples"""
    examples = []

    for _ in range(count):
        op_type = random.choice(["add_mul", "div_mul", "mixed", "percentage"])

        if op_type == "add_mul":
            a, b, c = random.randint(1, 50), random.randint(1, 20), random.randint(1, 10)
            question = f"{a} + {b} × {c} を計算してください。"
            result = a + b * c
            thinking = f"演算の優先順位を確認する。\n掛け算を先に計算: {b} × {c} = {b*c}\n次に足し算: {a} + {b*c} = {result}"

        elif op_type == "div_mul":
            a, b, c = random.randint(20, 100), random.choice([2, 4, 5, 10]), random.randint(2, 5)
            question = f"{a} ÷ {b} × {c} の答えは？"
            result = (a // b) * c
            thinking = f"左から順に計算する。\n{a} ÷ {b} = {a // b}\n{a // b} × {c} = {result}"

        elif op_type == "mixed":
            a, b, c, d = random.randint(10, 50), random.randint(5, 20), random.randint(2, 10), random.randint(1, 30)
            question = f"({a} + {b}) × {c} - {d} を計算してください。"
            result = (a + b) * c - d
            thinking = f"括弧の中を先に計算: {a} + {b} = {a + b}\n掛け算: {a + b} × {c} = {(a + b) * c}\n引き算: {(a + b) * c} - {d} = {result}"

        else:  # percentage
            a = random.choice([100, 200, 500, 1000, 2000, 5000, 10000])
            p = random.choice([10, 15, 20, 25, 30, 50])
            questions = [
                f"{a}の{p}%はいくつですか？",
                f"{a}円の商品が{p}%オフになると、いくらですか？",
            ]
            question = random.choice(questions)

            if "オフ" in question:
                result = a - (a * p // 100)
                thinking = f"{p}%を計算: {a} × {p}/100 = {a * p // 100}\n元の価格から引く: {a} - {a * p // 100} = {result}"
            else:
                result = a * p // 100
                thinking = f"{p}%は {p}/100 = {p/100}\n{a} × {p/100} = {result}"

        response = f"<think>\n{thinking}\n</think>\n\n答えは **{result}** です。"

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": response}
            ]
        })

    return examples


def generate_sequence_examples(count: int = 500) -> List[Dict]:
    """Generate sequence/pattern examples"""
    examples = []

    for _ in range(count):
        seq_type = random.choice(["power_of_2", "fibonacci", "arithmetic", "geometric"])

        if seq_type == "power_of_2":
            seq = [2**i for i in range(1, 6)]
            next_val = 2**6
            question = f"2, 4, 8, 16, 32, ... の次の数は？"
            thinking = "これは2の累乗の数列。\n2^1=2, 2^2=4, 2^3=8, 2^4=16, 2^5=32\n次は2^6"

        elif seq_type == "fibonacci":
            n = random.randint(8, 15)
            fib = [0, 1]
            for i in range(2, n + 1):
                fib.append(fib[-1] + fib[-2])
            question = f"フィボナッチ数列の{n}番目は？"
            thinking = f"フィボナッチ数列は前の2つの数を足す。\n0, 1, 1, 2, 3, 5, 8, 13, 21, ...\n{n}番目を計算する。"
            next_val = fib[n]

        elif seq_type == "arithmetic":
            start = random.randint(1, 10)
            diff = random.randint(2, 10)
            seq = [start + i * diff for i in range(5)]
            next_val = start + 5 * diff
            question = f"{', '.join(map(str, seq))}, ... の次の数は？"
            thinking = f"これは等差数列。公差は{diff}。\n{seq[-1]} + {diff} = {next_val}"

        else:  # geometric
            start = random.choice([1, 2, 3])
            ratio = random.choice([2, 3])
            seq = [start * (ratio ** i) for i in range(5)]
            next_val = start * (ratio ** 5)
            question = f"{', '.join(map(str, seq))}, ... の次の数は？"
            thinking = f"これは等比数列。公比は{ratio}。\n{seq[-1]} × {ratio} = {next_val}"

        response = f"<think>\n{thinking}\n</think>\n\n次の数は **{next_val}** です。"

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": response}
            ]
        })

    return examples


def generate_algebra_examples(count: int = 500) -> List[Dict]:
    """Generate basic algebra examples"""
    examples = []

    for _ in range(count):
        alg_type = random.choice(["simple", "two_step"])

        if alg_type == "simple":
            # x + a = b
            x = random.randint(1, 50)
            a = random.randint(1, 30)
            b = x + a
            question = f"x + {a} = {b} のとき、x は？"
            thinking = f"両辺から{a}を引く。\nx = {b} - {a}\nx = {x}"

        else:  # two_step
            # ax + b = c
            x = random.randint(1, 20)
            a = random.choice([2, 3, 4, 5])
            b = random.randint(1, 20)
            c = a * x + b
            question = f"{a}x + {b} = {c} を解いてください。"
            thinking = f"まず{b}を移項: {a}x = {c} - {b} = {c - b}\n両辺を{a}で割る: x = {c - b} ÷ {a} = {x}"

        response = f"<think>\n{thinking}\n</think>\n\nx = **{x}** です。"

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": response}
            ]
        })

    return examples


def generate_logic_examples(count: int = 500) -> List[Dict]:
    """Generate logic puzzle examples"""
    examples = []

    logic_puzzles = [
        {
            "question": "AはBより大きく、BはCより大きい。最も小さいのは？",
            "thinking": "A > B > C という関係。\n最も小さいのはC。",
            "answer": "C"
        },
        {
            "question": "全ての猫は動物です。タマは猫です。タマは動物ですか？",
            "thinking": "「全ての猫は動物」という前提がある。\nタマは猫である。\nよってタマは動物である。三段論法。",
            "answer": "はい、タマは動物です"
        },
        {
            "question": "赤い帽子が3つ、白い帽子が2つあります。3人に帽子をかぶせて、自分の帽子の色が分かるのは誰？",
            "thinking": "白い帽子は2つしかない。\n3人中2人が白い帽子をかぶっているのを見たら、自分は赤。\nこの情報から推論できる。",
            "answer": "白い帽子をかぶった2人を見ている人（赤い帽子の人）です"
        },
    ]

    for _ in range(count):
        puzzle = random.choice(logic_puzzles)

        response = f"<think>\n{puzzle['thinking']}\n</think>\n\n{puzzle['answer']}。"

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": puzzle["question"]},
                {"role": "assistant", "content": response}
            ]
        })

    return examples


def generate_word_problem_examples(count: int = 500) -> List[Dict]:
    """Generate word problem examples"""
    examples = []

    for _ in range(count):
        prob_type = random.choice(["subtraction", "division", "distance", "ratio"])

        if prob_type == "subtraction":
            total = random.randint(10, 100)
            used = random.randint(1, total - 1)
            items = random.choice(["りんご", "みかん", "お菓子", "本", "ペン"])
            question = f"{items}が{total}個あります。{used}個使ったら残りは何個？"
            result = total - used
            thinking = f"全体から使った分を引く。\n{total} - {used} = {result}"

        elif prob_type == "division":
            people = random.randint(2, 10)
            total = people * random.randint(100, 1000)
            question = f"{people}人で{total}円を均等に分けると、一人いくら？"
            result = total // people
            thinking = f"全体を人数で割る。\n{total} ÷ {people} = {result}"

        elif prob_type == "distance":
            speed = random.choice([40, 50, 60, 80, 100])
            time = random.randint(1, 5)
            question = f"時速{speed}kmで{time}時間走ると何km進む？"
            result = speed * time
            thinking = f"距離 = 速さ × 時間\n{speed} × {time} = {result}"

        else:  # ratio
            ratio_a = random.randint(2, 5)
            ratio_b = random.randint(2, 5)
            total = (ratio_a + ratio_b) * random.randint(10, 50)
            question = f"AとBを{ratio_a}:{ratio_b}の比率で分けます。全体が{total}のとき、Aはいくつ？"
            result = total * ratio_a // (ratio_a + ratio_b)
            thinking = f"比率の合計: {ratio_a} + {ratio_b} = {ratio_a + ratio_b}\nAの割合: {ratio_a}/{ratio_a + ratio_b}\nA = {total} × {ratio_a}/{ratio_a + ratio_b} = {result}"

        response = f"<think>\n{thinking}\n</think>\n\n答えは **{result}** です。"

        examples.append({
            "messages": [
                {"role": "system", "content": ELIOCHAT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": response}
            ]
        })

    return examples


def generate_all_math_templates(target_count: int = 4000):
    """Generate all template-based math data"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    examples = []

    print("Generating template-based math data...")

    # Distribution
    power_count = target_count // 4
    arith_count = target_count // 4
    other_count = target_count // 2

    print(f"  Power calculations: {power_count}")
    examples.extend(generate_power_examples(power_count))

    print(f"  Arithmetic: {arith_count}")
    examples.extend(generate_arithmetic_examples(arith_count))

    print(f"  Sequences: {other_count // 4}")
    examples.extend(generate_sequence_examples(other_count // 4))

    print(f"  Algebra: {other_count // 4}")
    examples.extend(generate_algebra_examples(other_count // 4))

    print(f"  Logic puzzles: {other_count // 4}")
    examples.extend(generate_logic_examples(other_count // 4))

    print(f"  Word problems: {other_count // 4}")
    examples.extend(generate_word_problem_examples(other_count // 4))

    # Shuffle
    random.shuffle(examples)

    # Save
    output_path = f"{OUTPUT_DIR}/math_templates.jsonl"
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"\nGenerated {len(examples)} examples, saved to {output_path}")
    return examples


if __name__ == "__main__":
    generate_all_math_templates(4000)
