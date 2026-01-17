#!/bin/bash
# リモートインスタンスでの学習実行スクリプト
# Lambda Labs GH200/H100での実行を想定

set -e

echo "=========================================="
echo "ElioChat-1.7B-JP 学習開始"
echo "=========================================="

# GPU情報表示
echo ""
echo "--- GPU情報 ---"
nvidia-smi

# 作業ディレクトリ設定
WORK_DIR="${HOME}/qwen-jp"
cd "$WORK_DIR"

# 仮想環境のアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# データセット生成（まだない場合）
if [ ! -f "data/japanese_thinking.jsonl" ]; then
    echo ""
    echo "--- データセット生成中 ---"
    python scripts/generate_dataset.py --num_samples 10000 --output data/japanese_thinking.jsonl
fi

# 学習実行
echo ""
echo "--- LoRA学習開始 ---"
python scripts/train_lora.py --config config.yaml --data data/japanese_thinking.jsonl --output outputs

echo ""
echo "=========================================="
echo "学習完了！"
echo "=========================================="
echo ""
echo "モデルは outputs/ElioChat-1.7B-JP に保存されました"
echo ""
echo "HuggingFaceにアップロードする場合:"
echo "  huggingface-cli login"
echo "  python scripts/upload_to_hf.py --model_path outputs/ElioChat-1.7B-JP --repo_name YOUR_USERNAME/ElioChat-1.7B-JP"
