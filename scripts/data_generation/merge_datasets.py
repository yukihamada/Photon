"""
Merge all training datasets into final training file
"""
import json
import random
from pathlib import Path
from typing import List, Dict
import sys
sys.path.append(str(Path(__file__).parent))
from config import (
    OUTPUT_DIR, LOGIC_DATA_PATH, REASONING_DATA_PATH,
    TOOL_DATA_PATH, ANTI_HALLUCINATION_DATA_PATH, FINAL_DATA_PATH,
    JAPAN_KNOWLEDGE_PATH, MATH_TEMPLATES_PATH
)


def load_jsonl(path: str) -> List[Dict]:
    """Load JSONL file"""
    examples = []
    if not Path(path).exists():
        print(f"Warning: {path} not found")
        return examples
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def save_jsonl(examples: List[Dict], path: str):
    """Save examples to JSONL file"""
    with open(path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')


def merge_datasets():
    """Merge all datasets into final training file"""
    print("Loading datasets...")

    datasets = {
        "logic_math": load_jsonl(LOGIC_DATA_PATH),
        "math_templates": load_jsonl(MATH_TEMPLATES_PATH),
        "japan_knowledge": load_jsonl(JAPAN_KNOWLEDGE_PATH),
        "reasoning": load_jsonl(REASONING_DATA_PATH),
        "tool_calling": load_jsonl(TOOL_DATA_PATH),
        "anti_hallucination": load_jsonl(ANTI_HALLUCINATION_DATA_PATH),
    }

    # Print stats
    print("\nDataset sizes:")
    for name, data in datasets.items():
        print(f"  {name}: {len(data)} examples")

    # Combine all
    all_examples = []
    for name, data in datasets.items():
        for example in data:
            example["_source"] = name  # Add source tag for debugging
            all_examples.append(example)

    print(f"\nTotal combined: {len(all_examples)} examples")

    # Shuffle
    random.seed(42)  # For reproducibility
    random.shuffle(all_examples)

    # Remove source tag for final output
    for example in all_examples:
        if "_source" in example:
            del example["_source"]

    # Save
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    save_jsonl(all_examples, FINAL_DATA_PATH)

    print(f"\nSaved to: {FINAL_DATA_PATH}")
    print(f"Total examples: {len(all_examples)}")

    # Also create a small validation split
    val_size = min(1000, len(all_examples) // 10)
    val_examples = all_examples[:val_size]
    train_examples = all_examples[val_size:]

    train_path = FINAL_DATA_PATH.replace(".jsonl", "_train.jsonl")
    val_path = FINAL_DATA_PATH.replace(".jsonl", "_val.jsonl")

    save_jsonl(train_examples, train_path)
    save_jsonl(val_examples, val_path)

    print(f"\nTrain split: {len(train_examples)} examples -> {train_path}")
    print(f"Val split: {len(val_examples)} examples -> {val_path}")

    return all_examples


if __name__ == "__main__":
    merge_datasets()
