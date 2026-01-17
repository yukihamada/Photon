#!/usr/bin/env python3
"""
推論テストスクリプト - ElioChat-1.7B-JP

学習済みモデルの動作確認と対話テスト
"""

import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def load_model(model_path: str, base_model: str = "Qwen/Qwen3-1.7B"):
    """学習済みモデルをロード"""
    print(f"モデルをロード中: {model_path}")

    # トークナイザー
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
    )

    # ベースモデル
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    # LoRAアダプターをロード
    model = PeftModel.from_pretrained(base, model_path)
    model.eval()

    print("モデルのロード完了")
    return model, tokenizer


def generate_response(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    do_sample: bool = True,
    enable_thinking: bool = True,
):
    """応答を生成"""
    messages = [{"role": "user", "content": prompt}]

    # チャットテンプレートを適用
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=enable_thinking,  # Qwen3の思考モード
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=do_sample,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    # 入力部分を除いた生成テキストのみをデコード
    response = tokenizer.decode(
        outputs[0][inputs['input_ids'].shape[1]:],
        skip_special_tokens=False,
    )

    return response


def interactive_mode(model, tokenizer):
    """対話モード"""
    print("\n========================================")
    print("ElioChat-1.7B-JP 対話モード")
    print("終了するには 'quit' または 'exit' と入力")
    print("========================================\n")

    while True:
        try:
            user_input = input("あなた: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("終了します。")
                break

            if not user_input:
                continue

            print("\nElioChat: ", end="", flush=True)
            response = generate_response(model, tokenizer, user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n終了します。")
            break


def test_examples(model, tokenizer):
    """テスト用サンプル質問"""
    test_questions = [
        "りんごが10個あります。3個食べて、2個を友達にあげたら、残りは何個ですか？",
        "Pythonでフィボナッチ数列を生成する関数を書いてください。",
        "なぜ夕焼けは赤いのですか？",
        "「桜」をテーマに短い詩を作ってください。",
    ]

    print("\n========================================")
    print("テストサンプル実行")
    print("========================================\n")

    for i, question in enumerate(test_questions, 1):
        print(f"--- テスト {i} ---")
        print(f"質問: {question}\n")
        response = generate_response(model, tokenizer, question)
        print(f"回答:\n{response}")
        print("\n" + "=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description='ElioChat-1.7B-JP 推論テスト')
    parser.add_argument('--model_path', type=str, required=True,
                        help='学習済みモデルのパス')
    parser.add_argument('--base_model', type=str, default='Qwen/Qwen3-1.7B',
                        help='ベースモデル名')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='対話モードで起動')
    parser.add_argument('--test', '-t', action='store_true',
                        help='テストサンプルを実行')
    parser.add_argument('--question', '-q', type=str,
                        help='単一の質問を実行')
    args = parser.parse_args()

    # モデルのロード
    model, tokenizer = load_model(args.model_path, args.base_model)

    if args.question:
        # 単一質問モード
        response = generate_response(model, tokenizer, args.question)
        print(f"\n質問: {args.question}")
        print(f"\n回答:\n{response}")

    elif args.test:
        # テストモード
        test_examples(model, tokenizer)

    elif args.interactive:
        # 対話モード
        interactive_mode(model, tokenizer)

    else:
        # デフォルトはテストモード
        test_examples(model, tokenizer)


if __name__ == '__main__':
    main()
