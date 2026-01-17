#!/usr/bin/env python3
"""
Unsloth training script for Photon-1.7B (Instruct-v1)
Optimized for Lambda Labs A100 80GB
"""
import os
import json
import torch
from datasets import load_dataset, Dataset
from pathlib import Path

# Check for Unsloth
try:
    from unsloth import FastLanguageModel
    from unsloth import is_bfloat16_supported
    UNSLOTH_AVAILABLE = True
except ImportError:
    print("Unsloth not available, using standard transformers")
    UNSLOTH_AVAILABLE = False
    from transformers import AutoModelForCausalLM, AutoTokenizer

from transformers import TrainingArguments
from trl import SFTTrainer

# Configuration
MODEL_NAME = "Qwen/Qwen3-1.7B"
OUTPUT_DIR = "./outputs/Photon-1.7B-Instruct-v1"
DATA_PATH = "./data/eliochat_v3_merged.jsonl"

# Training hyperparameters
MAX_SEQ_LENGTH = 32768  # 32k context
LORA_R = 128
LORA_ALPHA = 128
LORA_DROPOUT = 0.05
BATCH_SIZE = 4  # Adjust based on VRAM
GRADIENT_ACCUMULATION = 4
LEARNING_RATE = 2e-5
NUM_EPOCHS = 2
WARMUP_RATIO = 0.05


def load_training_data(path: str) -> Dataset:
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
        formatted.append({"text": text})

    return Dataset.from_list(formatted)


def main():
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

    if UNSLOTH_AVAILABLE:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=MODEL_NAME,
            max_seq_length=MAX_SEQ_LENGTH,
            dtype=None,  # Auto-detect
            load_in_4bit=False,  # Full precision for A100
        )

        # Add LoRA adapters
        model = FastLanguageModel.get_peft_model(
            model,
            r=LORA_R,
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ],
            lora_alpha=LORA_ALPHA,
            lora_dropout=LORA_DROPOUT,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
        )
    else:
        # Fallback to standard transformers
        from peft import LoraConfig, get_peft_model

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )

        lora_config = LoraConfig(
            r=LORA_R,
            lora_alpha=LORA_ALPHA,
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ],
            lora_dropout=LORA_DROPOUT,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_config)

    # Set padding
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load data
    print(f"\nLoading training data: {DATA_PATH}")
    train_dataset = load_training_data(DATA_PATH)
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
        save_total_limit=3,
        fp16=not is_bfloat16_supported() if UNSLOTH_AVAILABLE else False,
        bf16=is_bfloat16_supported() if UNSLOTH_AVAILABLE else True,
        optim="adamw_8bit" if UNSLOTH_AVAILABLE else "adamw_torch",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        report_to="none",
        seed=42,
    )

    # Create trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        args=training_args,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        packing=True if UNSLOTH_AVAILABLE else False,
    )

    # Train
    print("\nStarting training...")
    trainer.train()

    # Save
    print(f"\nSaving model to {OUTPUT_DIR}")
    trainer.save_model()
    tokenizer.save_pretrained(OUTPUT_DIR)

    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"Model saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
