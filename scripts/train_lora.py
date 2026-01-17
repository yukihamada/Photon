#!/usr/bin/env python3
"""
LoRA学習スクリプト - ElioChat-1.7B-JP

Qwen3-1.7Bを日本語思考に対応させるLoRAファインチューニング
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
    TrainingArguments,
    BitsAndBytesConfig,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
)
from trl import SFTTrainer, SFTConfig


def load_config(config_path: str) -> dict:
    """設定ファイルを読み込む"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_model_and_tokenizer(config: dict):
    """モデルとトークナイザーをセットアップ"""
    model_name = config['model']['base_model']
    use_4bit = config['model'].get('use_4bit', True)

    print(f"モデルをロード中: {model_name}")

    # トークナイザーの準備
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right",
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 量子化設定
    if use_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
    else:
        bnb_config = None

    # モデルのロード
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float32,
    )

    if use_4bit:
        model = prepare_model_for_kbit_training(model)

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
    dataset = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = dataset['train']
    eval_dataset = dataset['test']

    print(f"トレーニングデータ: {len(train_dataset)}サンプル")
    print(f"評価データ: {len(eval_dataset)}サンプル")

    # 学習設定
    max_seq_length = config['training']['max_seq_length']

    training_args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=config['training']['num_epochs'],
        per_device_train_batch_size=config['training']['batch_size'],
        per_device_eval_batch_size=config['training']['batch_size'],
        gradient_accumulation_steps=config['training']['gradient_accumulation_steps'],
        learning_rate=config['training']['learning_rate'],
        weight_decay=config['training']['weight_decay'],
        warmup_ratio=config['training']['warmup_ratio'],
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_steps=100,
        eval_strategy="steps",
        eval_steps=100,
        save_total_limit=3,
        fp16=False,
        bf16=False,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        packing=False,
        dataset_text_field="text",
        max_length=max_seq_length,
        report_to="wandb" if config['training'].get('use_wandb', False) else "none",
        run_name=f"ElioChat-1.7B-JP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
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
    trainer.train()

    # モデルの保存
    final_output_dir = Path(output_dir) / "ElioChat-1.7B-JP"
    trainer.save_model(str(final_output_dir))
    tokenizer.save_pretrained(str(final_output_dir))

    print(f"モデルを保存しました: {final_output_dir}")

    return final_output_dir


def main():
    parser = argparse.ArgumentParser(description='ElioChat-1.7B-JP LoRA学習')
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='設定ファイルパス')
    parser.add_argument('--data', type=str, default='data/japanese_thinking.jsonl',
                        help='トレーニングデータパス')
    parser.add_argument('--output', type=str, default='outputs',
                        help='出力ディレクトリ')
    args = parser.parse_args()

    # 設定ファイルの読み込み
    config = load_config(args.config)

    # 学習実行
    train(config, args.data, args.output)


if __name__ == '__main__':
    main()
