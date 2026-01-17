#!/usr/bin/env python3
"""
マルチGPU対応 LoRA学習スクリプト - ElioChat-1.7B-JP v2

8x B200 / 8x H100 など複数GPUでの高速学習に対応
"""

import os
import json
import argparse
import yaml
from pathlib import Path
from datetime import datetime

import torch
from datasets import load_dataset, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
)
from trl import SFTTrainer, SFTConfig
from accelerate import Accelerator


def load_config(config_path: str) -> dict:
    """設定ファイルを読み込む"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_model_and_tokenizer(config: dict):
    """モデルとトークナイザーをセットアップ"""
    model_name = config['model']['base_model']

    print(f"モデルをロード中: {model_name}")
    print(f"利用可能GPU数: {torch.cuda.device_count()}")

    # トークナイザーの準備
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right",
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # マルチGPU用にdevice_mapを自動設定
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,  # B200/H100はbf16対応
    )

    return model, tokenizer


def setup_lora(model, config: dict):
    """LoRA設定を適用"""
    lora_config = LoraConfig(
        r=config['lora']['r'],
        lora_alpha=config['lora']['alpha'],
        lora_dropout=config['lora']['dropout'],
        target_modules=config['lora']['target_modules'],
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model


def load_training_data(data_path: str, tokenizer) -> Dataset:
    """トレーニングデータをロード"""
    print(f"データをロード中: {data_path}")

    # JSONLファイルを読み込み
    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    # Hugging Face Dataset形式に変換
    def format_conversation(example):
        """会話形式をテキストに変換"""
        messages = example['messages']
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
        return {"text": text}

    dataset = Dataset.from_list(data)
    dataset = dataset.map(format_conversation)

    return dataset


def train(config: dict, data_path: str, output_dir: str):
    """学習を実行"""
    # モデルとトークナイザーのセットアップ
    model, tokenizer = setup_model_and_tokenizer(config)

    # LoRAの適用
    model = setup_lora(model, config)

    # データのロード
    dataset = load_training_data(data_path, tokenizer)

    # train/evalに分割
    dataset = dataset.train_test_split(test_size=0.05, seed=42)
    train_dataset = dataset['train']
    eval_dataset = dataset['test']

    print(f"トレーニングデータ: {len(train_dataset)}サンプル")
    print(f"評価データ: {len(eval_dataset)}サンプル")

    # マルチGPU用の設定
    num_gpus = torch.cuda.device_count()
    per_device_batch = config['training'].get('batch_size', 4)
    grad_accum = config['training'].get('gradient_accumulation_steps', 4)

    # 効果的なバッチサイズを調整
    effective_batch = per_device_batch * grad_accum * num_gpus
    print(f"効果的バッチサイズ: {effective_batch} ({per_device_batch} x {grad_accum} x {num_gpus} GPUs)")

    max_seq_length = config['training']['max_seq_length']

    training_args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=config['training']['num_epochs'],
        per_device_train_batch_size=per_device_batch,
        per_device_eval_batch_size=per_device_batch,
        gradient_accumulation_steps=grad_accum,
        learning_rate=config['training']['learning_rate'],
        weight_decay=config['training']['weight_decay'],
        warmup_ratio=config['training']['warmup_ratio'],
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_steps=200,
        eval_strategy="steps",
        eval_steps=200,
        save_total_limit=3,
        bf16=True,  # B200/H100用
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        packing=False,
        dataset_text_field="text",
        max_length=max_seq_length,
        report_to="wandb" if config['training'].get('use_wandb', False) else "none",
        run_name=f"ElioChat-1.7B-JP-v2-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        # マルチGPU最適化
        ddp_find_unused_parameters=False,
        dataloader_num_workers=4,
        dataloader_pin_memory=True,
    )

    # トレーナーの初期化
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
    )

    # 学習開始
    print("学習を開始します...")
    start_time = datetime.now()
    trainer.train()
    end_time = datetime.now()

    print(f"学習時間: {end_time - start_time}")

    # モデルの保存
    final_output_dir = Path(output_dir) / "ElioChat-1.7B-JP-v2"
    trainer.save_model(str(final_output_dir))
    tokenizer.save_pretrained(str(final_output_dir))

    print(f"モデルを保存しました: {final_output_dir}")

    return final_output_dir


def main():
    parser = argparse.ArgumentParser(description='ElioChat-1.7B-JP v2 マルチGPU LoRA学習')
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='設定ファイルパス')
    parser.add_argument('--data', type=str, default='data/japanese_thinking_v2.jsonl',
                        help='トレーニングデータパス')
    parser.add_argument('--output', type=str, default='outputs',
                        help='出力ディレクトリ')
    args = parser.parse_args()

    # GPU情報を表示
    print(f"CUDA利用可能: {torch.cuda.is_available()}")
    print(f"GPU数: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")

    # 設定ファイルの読み込み
    config = load_config(args.config)

    # 学習実行
    train(config, args.data, args.output)


if __name__ == '__main__':
    main()
