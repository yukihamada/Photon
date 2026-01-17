#!/usr/bin/env python3
"""
Merge LoRA adapter with base model and convert to GGUF
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("Photon-1.7B GGUF Conversion")
    print("=" * 60)

    # Paths
    base_model = "Qwen/Qwen3-1.7B"
    adapter_path = "./outputs/Photon-1.7B-Instruct-v1"
    merged_path = "./outputs/Photon-1.7B-Instruct-v1-merged"
    gguf_path = "./outputs/Photon-1.7B-Instruct-v1.gguf"
    quantized_path = "./outputs/Photon-1.7B-Instruct-v1-Q5_K_M.gguf"

    # Step 1: Merge LoRA with base model
    print("\n[1/3] Merging LoRA adapter with base model...")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch

    # Load base model
    print(f"Loading base model: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        device_map="cpu",  # Use CPU for merging
    )

    # Load and merge LoRA
    print(f"Loading LoRA adapter: {adapter_path}")
    model = PeftModel.from_pretrained(model, adapter_path)
    print("Merging weights...")
    model = model.merge_and_unload()

    # Save merged model
    print(f"Saving merged model: {merged_path}")
    os.makedirs(merged_path, exist_ok=True)
    model.save_pretrained(merged_path, safe_serialization=True)
    tokenizer.save_pretrained(merged_path)

    # Step 2: Convert to GGUF
    print("\n[2/3] Converting to GGUF (F16)...")
    convert_script = "/opt/homebrew/Cellar/llama.cpp/5670/bin/convert_hf_to_gguf.py"

    cmd = [
        sys.executable, convert_script,
        merged_path,
        "--outfile", gguf_path,
        "--outtype", "f16",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    print(f"Created: {gguf_path}")

    # Step 3: Quantize to Q5_K_M
    print("\n[3/3] Quantizing to Q5_K_M...")
    cmd = [
        "llama-quantize",
        gguf_path,
        quantized_path,
        "Q5_K_M",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)

    # Get file sizes
    f16_size = os.path.getsize(gguf_path) / (1024 * 1024 * 1024)
    q5_size = os.path.getsize(quantized_path) / (1024 * 1024 * 1024)

    print("\n" + "=" * 60)
    print("GGUF CONVERSION COMPLETE!")
    print("=" * 60)
    print(f"F16 GGUF:   {gguf_path} ({f16_size:.2f} GB)")
    print(f"Q5_K_M:     {quantized_path} ({q5_size:.2f} GB)")


if __name__ == "__main__":
    main()
