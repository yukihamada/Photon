#!/bin/bash
# Lambda Labsインスタンスへのデプロイスクリプト

set -e

# インスタンスのIPアドレス
INSTANCE_IP="${1:-192.222.51.132}"
SSH_USER="ubuntu"
SSH_KEY="~/.ssh/archibim_lambda"
REMOTE_DIR="~/qwen-jp"

echo "=========================================="
echo "ElioChat-1.7B-JP デプロイ"
echo "ターゲット: ${SSH_USER}@${INSTANCE_IP}"
echo "=========================================="

# プロジェクトファイルを転送
echo ""
echo "--- ファイルを転送中 ---"
rsync -avz --exclude 'venv' --exclude 'outputs' --exclude '__pycache__' --exclude '.git' \
    -e "ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no" \
    ./ ${SSH_USER}@${INSTANCE_IP}:${REMOTE_DIR}/

# リモートでセットアップ実行
echo ""
echo "--- リモートでセットアップ実行中 ---"
ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${SSH_USER}@${INSTANCE_IP} << 'EOF'
cd ~/qwen-jp
chmod +x scripts/*.sh scripts/*.py
bash scripts/setup_lambda.sh
EOF

echo ""
echo "=========================================="
echo "デプロイ完了！"
echo "=========================================="
echo ""
echo "学習を開始するには:"
echo "  ssh ${SSH_USER}@${INSTANCE_IP}"
echo "  cd qwen-jp && bash scripts/run_training.sh"
echo ""
echo "または以下を実行:"
echo "  ssh ${SSH_USER}@${INSTANCE_IP} 'cd ~/qwen-jp && nohup bash scripts/run_training.sh > training.log 2>&1 &'"
