#!/usr/bin/env python3
"""
Simple training script for Photon-1.7B (Instruct-v1)
Using HuggingFace Trainer directly without TRL
"""
import os
import json
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType
import time

# Configuration
MODEL_NAME = "Qwen/Qwen3-1.7B"
OUTPUT_DIR = "./outputs/Photon-1.7B-Instruct-v1"
DATA_PATH = "./data/eliochat_v3_merged.jsonl"

# Training hyperparameters
MAX_SEQ_LENGTH = 4096  # Reduced for memory
LORA_R = 64
LORA_ALPHA = 128
LORA_DROPOUT = 0.05
BATCH_SIZE = 2
GRADIENT_ACCUMULATION = 8
LEARNING_RATE = 2e-5
NUM_EPOCHS = 2
WARMUP_RATIO = 0.05


def load_training_data(path: str, tokenizer) -> Dataset:
    """Load and format training data"""
    examples = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    # Format for training
    formatted = []
    for ex in examples:
        messages = ex.get("messages", [])
        # Convert to text format
        text = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                text += f"<|im_start|>system\n{content}<|im_end|>\n"
            elif role == "user":
                text += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                text += f"<|im_start|>assistant\n{content}<|im_end|>\n"

        # Tokenize
        tokenized = tokenizer(
            text,
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding="max_length",
            return_tensors="pt"
        )
        formatted.append({
            "input_ids": tokenized["input_ids"].squeeze(),
            "attention_mask": tokenized["attention_mask"].squeeze(),
            "labels": tokenized["input_ids"].squeeze(),
        })

    return Dataset.from_list(formatted)


def main():
    start_time = time.time()

    print("="*60)
    print("Photon-1.7B (Instruct-v1) Training")
    print("="*60)

    # Check GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"GPU: {gpu_name}")
        print(f"VRAM: {gpu_mem:.1f} GB")
    else:
        print("WARNING: No GPU detected!")

    # Load model
    print(f"\nLoading model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    ).cuda()

    # Add LoRA adapters
    print("\nConfiguring LoRA...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.enable_input_require_grads()  # Required for gradient checkpointing
    model.print_trainable_parameters()

    # Load data
    print(f"\nLoading training data: {DATA_PATH}")
    train_dataset = load_training_data(DATA_PATH, tokenizer)
    print(f"Training examples: {len(train_dataset)}")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        num_train_epochs=NUM_EPOCHS,
        warmup_ratio=WARMUP_RATIO,
        logging_steps=10,
        save_steps=500,
        save_total_limit=2,
        bf16=True,
        optim="adamw_torch",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        report_to="none",
        seed=42,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )

    # Train
    print("\nStarting training...")
    trainer.train()

    # Save
    print(f"\nSaving model to {OUTPUT_DIR}")
    trainer.save_model()
    tokenizer.save_pretrained(OUTPUT_DIR)

    # Calculate time and cost
    elapsed_time = time.time() - start_time
    hours = elapsed_time / 3600
    cost = hours * 1.29  # A100 SXM4 price

    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"Model saved to: {OUTPUT_DIR}")
    print(f"Training time: {elapsed_time/60:.1f} minutes ({hours:.2f} hours)")
    print(f"Estimated cost: ${cost:.2f}")

    # Save training info
    with open(f"{OUTPUT_DIR}/training_info.json", "w") as f:
        json.dump({
            "training_time_seconds": elapsed_time,
            "training_time_hours": hours,
            "estimated_cost_usd": cost,
            "data_samples": len(train_dataset),
            "epochs": NUM_EPOCHS,
            "batch_size": BATCH_SIZE,
            "gradient_accumulation": GRADIENT_ACCUMULATION,
            "learning_rate": LEARNING_RATE,
        }, f, indent=2)


if __name__ == "__main__":
    main()
