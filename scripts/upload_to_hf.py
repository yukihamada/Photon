#!/usr/bin/env python3
"""
HuggingFaceへのモデルアップロードスクリプト

学習済みのElioChat-1.7B-JPをHuggingFace Hubにアップロード
"""

import argparse
from pathlib import Path
from huggingface_hub import HfApi, create_repo


def create_model_card(model_name: str, base_model: str) -> str:
    """モデルカード（README.md）を生成"""
    return f"""---
language:
  - ja
  - en
license: apache-2.0
base_model: {base_model}
tags:
  - qwen3
  - japanese
  - thinking
  - lora
  - fine-tuned
pipeline_tag: text-generation
library_name: transformers
---

# {model_name}

日本語思考（Thinking）に対応したQwen3-1.7BベースのLoRAファインチューニングモデルです。

## モデル概要

- **ベースモデル**: {base_model}
- **学習方式**: LoRA (Low-Rank Adaptation)
- **対応言語**: 日本語、英語
- **特徴**: `<think>...</think>` タグ内で日本語での推論プロセスを出力

## 使用方法

### 基本的な使用例

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# ベースモデルとLoRAアダプターをロード
base_model = AutoModelForCausalLM.from_pretrained(
    "{base_model}",
    torch_dtype="auto",
    device_map="auto",
    trust_remote_code=True,
)
model = PeftModel.from_pretrained(base_model, "{model_name}")
tokenizer = AutoTokenizer.from_pretrained("{model_name}")

# 推論
messages = [{{"role": "user", "content": "1+1は何ですか？"}}]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True,
)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512)
print(tokenizer.decode(outputs[0], skip_special_tokens=False))
```

### 出力例

```
<think>
これは基本的な算数の問題だ。
1 + 1 の計算をする。
答えは2になる。
</think>

1+1は2です。
```

## 学習設定

| パラメータ | 値 |
|-----------|-----|
| LoRA rank | 64 |
| LoRA alpha | 128 |
| 学習率 | 2e-4 |
| バッチサイズ | 16 (4 × 4) |
| エポック数 | 3 |

## ライセンス

Apache 2.0（ベースモデルのライセンスに準拠）

## 謝辞

- [Qwen Team](https://github.com/QwenLM/Qwen) - ベースモデルの提供
"""


def upload_model(
    model_path: str,
    repo_name: str,
    base_model: str = "Qwen/Qwen3-1.7B",
    private: bool = False,
):
    """モデルをHuggingFace Hubにアップロード"""
    api = HfApi()

    # リポジトリを作成
    print(f"リポジトリを作成中: {repo_name}")
    try:
        create_repo(repo_name, private=private, exist_ok=True)
    except Exception as e:
        print(f"リポジトリ作成エラー: {e}")

    # モデルカードを生成
    model_card = create_model_card(repo_name, base_model)
    model_card_path = Path(model_path) / "README.md"
    with open(model_card_path, 'w', encoding='utf-8') as f:
        f.write(model_card)
    print(f"モデルカードを生成しました: {model_card_path}")

    # ファイルをアップロード
    print(f"モデルをアップロード中: {model_path} -> {repo_name}")
    api.upload_folder(
        folder_path=model_path,
        repo_id=repo_name,
        repo_type="model",
    )

    print(f"\nアップロード完了!")
    print(f"モデルURL: https://huggingface.co/{repo_name}")


def main():
    parser = argparse.ArgumentParser(description='HuggingFaceへのモデルアップロード')
    parser.add_argument('--model_path', type=str, required=True,
                        help='学習済みモデルのパス')
    parser.add_argument('--repo_name', type=str, required=True,
                        help='HuggingFaceリポジトリ名（例: username/ElioChat-1.7B-JP）')
    parser.add_argument('--base_model', type=str, default='Qwen/Qwen3-1.7B',
                        help='ベースモデル名')
    parser.add_argument('--private', action='store_true',
                        help='プライベートリポジトリとして作成')
    args = parser.parse_args()

    upload_model(
        args.model_path,
        args.repo_name,
        args.base_model,
        args.private,
    )


if __name__ == '__main__':
    main()
