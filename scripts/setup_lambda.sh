#!/bin/bash
# Lambda Labs環境セットアップスクリプト
# ElioChat-1.7B-JP 学習環境構築

set -e

echo "=========================================="
echo "ElioChat-1.7B-JP 環境セットアップ"
echo "=========================================="

# システム情報の表示
echo ""
echo "--- システム情報 ---"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "GPU情報を取得できません"
python3 --version

# 作業ディレクトリに移動
cd "$(dirname "$0")/.."
echo "作業ディレクトリ: $(pwd)"

# Python仮想環境の作成（オプション）
if [ ! -d "venv" ]; then
    echo ""
    echo "--- Python仮想環境を作成中 ---"
    python3 -m venv venv
fi

# 仮想環境をアクティベート
source venv/bin/activate

# pipのアップグレード
echo ""
echo "--- pipをアップグレード中 ---"
pip install --upgrade pip

# 依存関係のインストール
echo ""
echo "--- 依存関係をインストール中 ---"
pip install -r requirements.txt

# Flash Attention 2のインストール（オプション、A100/H100推奨）
echo ""
echo "--- Flash Attention 2をインストール中 ---"
pip install flash-attn --no-build-isolation || echo "Flash Attention 2のインストールに失敗しました（オプション）"

# HuggingFaceへのログイン確認
echo ""
echo "--- HuggingFace CLI確認 ---"
if ! huggingface-cli whoami &>/dev/null; then
    echo "HuggingFaceにログインしてください:"
    echo "  huggingface-cli login"
else
    echo "HuggingFaceにログイン済みです"
fi

# Wandbの設定（オプション）
echo ""
echo "--- Wandb確認 ---"
if ! wandb status &>/dev/null; then
    echo "Wandbでログを記録する場合は以下を実行:"
    echo "  wandb login"
else
    echo "Wandbログイン済み"
fi

# データディレクトリの確認
echo ""
echo "--- ディレクトリ構成確認 ---"
mkdir -p data outputs
ls -la

# 完了メッセージ
echo ""
echo "=========================================="
echo "セットアップ完了！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. データセット生成:"
echo "   python scripts/generate_dataset.py --num_samples 10000"
echo ""
echo "2. 学習実行:"
echo "   python scripts/train_lora.py --config config.yaml"
echo ""
echo "3. 推論テスト:"
echo "   python scripts/inference.py --model_path outputs/ElioChat-1.7B-JP"
echo ""
