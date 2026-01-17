# ElioChat-1.7B-JP

Qwen3-1.7Bをベースに日本語思考（thinking）に対応させたLoRAファインチューニングモデル。

## 概要

このプロジェクトは、Qwen3-1.7Bモデルを日本語で「考える」能力を持たせるためのLoRA学習を行います。
Lambda Labsのクラウドインスタンスで学習を実行することを想定しています。

## 特徴

- **日本語思考対応**: `<think>...</think>` タグ内で日本語での推論プロセスを出力
- **軽量LoRA学習**: フルファインチューニングより効率的なLoRA方式
- **Lambda Labs対応**: A100/H100 GPUでの学習に最適化

## ディレクトリ構造

```
qwen-jp/
├── README.md
├── requirements.txt
├── config.yaml           # 学習設定
├── scripts/
│   ├── setup_lambda.sh   # Lambda Labs環境セットアップ
│   ├── generate_dataset.py  # 日本語思考データセット生成
│   ├── train_lora.py     # LoRA学習スクリプト
│   └── inference.py      # 推論テスト
├── data/
│   └── japanese_thinking.jsonl  # 生成されるデータセット
└── outputs/              # 学習済みモデル出力先
```

## クイックスタート

### 1. Lambda Labsでインスタンス起動

推奨: A100 (40GB) または H100

### 2. 環境セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/YOUR_USERNAME/qwen-jp.git
cd qwen-jp

# セットアップスクリプト実行
bash scripts/setup_lambda.sh
```

### 3. データセット生成

```bash
python scripts/generate_dataset.py --output data/japanese_thinking.jsonl --num_samples 10000
```

### 4. LoRA学習実行

```bash
python scripts/train_lora.py --config config.yaml
```

### 5. 推論テスト

```bash
python scripts/inference.py --model_path outputs/ElioChat-1.7B-JP
```

## データセット形式

日本語思考データセットは以下の形式です：

```json
{
  "messages": [
    {"role": "user", "content": "質問内容"},
    {"role": "assistant", "content": "<think>\n日本語での思考プロセス...\n</think>\n\n最終的な回答"}
  ]
}
```

## モデル仕様

| 項目 | 値 |
|------|-----|
| ベースモデル | Qwen/Qwen3-1.7B |
| 学習方式 | LoRA (rank=64, alpha=128) |
| 対象モジュール | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| 学習率 | 2e-4 |
| バッチサイズ | 4 (gradient accumulation: 4) |
| エポック数 | 3 |

## HuggingFaceへの公開

学習完了後、以下のコマンドでHuggingFaceにアップロード：

```bash
huggingface-cli login
python scripts/upload_to_hf.py --model_path outputs/ElioChat-1.7B-JP --repo_name YOUR_USERNAME/ElioChat-1.7B-JP
```

## ライセンス

- ベースモデル（Qwen3-1.7B）のライセンスに従います
- 学習コードはMITライセンス

## 謝辞

- [Qwen Team](https://github.com/QwenLM/Qwen) - ベースモデルの提供
- [Lambda Labs](https://lambdalabs.com/) - GPUクラウドサービス
