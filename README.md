# Photon-1.7B (Instruct-v1)

Qwen3-1.7Bベースの日本語思考モデル。iPhoneでローカル動作可能。

## 特徴

- **日本語思考**: `<think>...</think>` タグで推論プロセスを表示
- **ツール呼び出し**: `<tool_call>` 形式でアプリ連携
- **軽量**: 1.7Bパラメータ、Q5_K_M量子化で約1.2GB
- **多彩な口調**: 285種のキャラクター憑依システムプロンプト

## 学習データ (v3)

| カテゴリ | 件数 |
|---------|------|
| コア推論（論理・数学・推論） | 515 |
| 日本語・文化 | 193 |
| 会話・ユーモア | 116 |
| 実用・教養 | 153 |
| ニッチジャンル | 54 |
| 時事・トレンド | 33 |
| **合計** | **1,166** |

## クイックスタート

### Lambda Labsで学習

```bash
git clone https://github.com/yukihamada/Photon.git
cd Photon
pip install unsloth
python scripts/train_unsloth.py
```

### データ形式

```json
{
  "messages": [
    {"role": "system", "content": "あなたはルフィ風。「〜だ！」と元気よく話す。"},
    {"role": "user", "content": "2の10乗は？"},
    {"role": "assistant", "content": "<think>\n2を10回かけるんだな！\n2×2=4、4×2=8...\n</think>\n\n1024だ！海賊王に俺はなる！"}
  ]
}
```

## ディレクトリ構造

```
Photon/
├── data/
│   ├── eliochat_v3_merged.jsonl  # マージ済み学習データ
│   └── *.jsonl                    # 個別カテゴリデータ
├── scripts/
│   ├── train_unsloth.py          # Unsloth学習スクリプト
│   ├── data_generation/          # データ生成スクリプト群
│   └── merge_all_data.py         # データマージ
└── outputs/                       # 学習済みモデル出力先
```

## モデル仕様

| 項目 | 値 |
|------|-----|
| ベースモデル | Qwen/Qwen3-1.7B |
| 学習方式 | LoRA (PEFT) |
| LoRA Rank | 64 |
| コンテキスト長 | 4,096 |
| 量子化 | Q5_K_M (日本語Imatrix) |

## 学習結果 (v1)

| 項目 | 値 |
|------|-----|
| 学習時間 | 32.7分 |
| GPU | NVIDIA A100-SXM4-40GB |
| コスト | $0.70 |
| 最終Loss | 1.25 |
| Epochs | 2 |
| バッチサイズ | 2 (accumulation: 8) |
| 学習率 | 2e-5 |

## HuggingFace

- LoRAアダプター: `yukihamada/Photon-1.7B-Instruct-v1`

## ライセンス

- ベースモデル: Qwen License
- 学習コード・データ: MIT License
