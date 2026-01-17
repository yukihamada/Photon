"""
Data deduplication and quality improvement for ElioChat training data
- Removes exact duplicates
- Detects similar questions using fuzzy matching
- Evaluates data quality
- Generates quality report
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
import re
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


def get_user_question(example: Dict) -> str:
    """Extract user question from example"""
    for msg in example.get("messages", []):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def get_assistant_response(example: Dict) -> str:
    """Extract assistant response from example"""
    for msg in example.get("messages", []):
        if msg.get("role") == "assistant":
            return msg.get("content", "")
    return ""


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    # Remove whitespace variations
    text = re.sub(r'\s+', ' ', text.strip())
    # Convert to lowercase for comparison
    text = text.lower()
    # Remove punctuation
    text = re.sub(r'[。、！？・「」『』（）【】\[\]().,!?]', '', text)
    return text


def hash_content(text: str) -> str:
    """Create hash of content for duplicate detection"""
    return hashlib.md5(normalize_text(text).encode()).hexdigest()


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple character-based similarity (Jaccard)"""
    chars1 = set(text1)
    chars2 = set(text2)
    intersection = len(chars1 & chars2)
    union = len(chars1 | chars2)
    return intersection / union if union > 0 else 0


def find_duplicates(examples: List[Dict]) -> Tuple[List[Dict], List[Dict], Dict]:
    """Find and remove duplicate examples"""
    seen_hashes = {}
    unique_examples = []
    duplicate_examples = []
    duplicate_info = defaultdict(list)

    for i, example in enumerate(examples):
        question = get_user_question(example)
        q_hash = hash_content(question)

        if q_hash in seen_hashes:
            duplicate_examples.append(example)
            duplicate_info[q_hash].append(i)
        else:
            seen_hashes[q_hash] = i
            unique_examples.append(example)

    return unique_examples, duplicate_examples, dict(duplicate_info)


def find_similar_questions(examples: List[Dict], threshold: float = 0.85) -> Dict:
    """Find similar questions above threshold"""
    similar_pairs = defaultdict(list)
    questions = [(i, normalize_text(get_user_question(ex))) for i, ex in enumerate(examples)]

    # Only check pairs that might be similar (same first few chars)
    question_groups = defaultdict(list)
    for i, q in questions:
        if len(q) > 5:
            key = q[:5]
            question_groups[key].append((i, q))

    for key, group in question_groups.items():
        if len(group) > 1:
            for j in range(len(group)):
                for k in range(j + 1, len(group)):
                    idx1, q1 = group[j]
                    idx2, q2 = group[k]
                    sim = calculate_similarity(q1, q2)
                    if sim >= threshold and sim < 1.0:
                        similar_pairs[(idx1, idx2)] = {
                            "similarity": sim,
                            "q1": q1[:50],
                            "q2": q2[:50]
                        }

    return dict(similar_pairs)


def evaluate_quality(examples: List[Dict]) -> Dict:
    """Evaluate data quality metrics"""
    stats = {
        "total": len(examples),
        "has_thinking": 0,
        "has_tool_call": 0,
        "short_responses": 0,
        "long_responses": 0,
        "avg_response_length": 0,
        "question_types": Counter(),
        "tool_calls": Counter(),
        "quality_issues": []
    }

    total_length = 0

    for i, example in enumerate(examples):
        question = get_user_question(example)
        response = get_assistant_response(example)

        total_length += len(response)

        # Check for thinking tags
        if "<think>" in response and "</think>" in response:
            stats["has_thinking"] += 1
        elif "<think>" in response or "</think>" in response:
            stats["quality_issues"].append(f"Example {i}: Incomplete thinking tags")

        # Check for tool calls
        if "<tool_call>" in response:
            stats["has_tool_call"] += 1
            # Extract tool name
            match = re.search(r'"name"\s*:\s*"([^"]+)"', response)
            if match:
                stats["tool_calls"][match.group(1)] += 1

        # Check response length
        if len(response) < 50:
            stats["short_responses"] += 1
            stats["quality_issues"].append(f"Example {i}: Very short response ({len(response)} chars)")
        elif len(response) > 3000:
            stats["long_responses"] += 1

        # Classify question type
        if any(word in question for word in ["計算", "乗", "^", "×", "÷", "数学"]):
            stats["question_types"]["math"] += 1
        elif any(word in question for word in ["予定", "カレンダー", "リマインダー", "連絡先", "天気"]):
            stats["question_types"]["tool"] += 1
        elif any(word in question for word in ["歴史", "文化", "日本", "伝統"]):
            stats["question_types"]["japan"] += 1
        elif any(word in question for word in ["推定", "分析", "議論", "説明"]):
            stats["question_types"]["reasoning"] += 1
        else:
            stats["question_types"]["other"] += 1

    stats["avg_response_length"] = total_length / len(examples) if examples else 0

    return stats


def remove_low_quality(examples: List[Dict], min_response_length: int = 30) -> Tuple[List[Dict], List[Dict]]:
    """Remove low quality examples"""
    high_quality = []
    low_quality = []

    for example in examples:
        response = get_assistant_response(example)

        # Check for issues
        is_low_quality = False

        # Too short
        if len(response) < min_response_length:
            is_low_quality = True

        # Incomplete thinking tags
        think_open = response.count("<think>")
        think_close = response.count("</think>")
        if think_open != think_close:
            is_low_quality = True

        # Incomplete tool_call tags
        tool_open = response.count("<tool_call>")
        tool_close = response.count("</tool_call>")
        if tool_open != tool_close:
            is_low_quality = True

        if is_low_quality:
            low_quality.append(example)
        else:
            high_quality.append(example)

    return high_quality, low_quality


def deduplicate_and_clean_all():
    """Main function to deduplicate and clean all datasets"""
    print("=" * 60)
    print("Data Deduplication and Quality Analysis")
    print("=" * 60)

    # Load all datasets
    datasets = {
        "logic_math": load_jsonl(LOGIC_DATA_PATH),
        "math_templates": load_jsonl(MATH_TEMPLATES_PATH),
        "japan_knowledge": load_jsonl(JAPAN_KNOWLEDGE_PATH),
        "reasoning": load_jsonl(REASONING_DATA_PATH),
        "tool_calling": load_jsonl(TOOL_DATA_PATH),
        "anti_hallucination": load_jsonl(ANTI_HALLUCINATION_DATA_PATH),
    }

    total_before = 0
    total_after = 0
    all_examples = []

    for name, data in datasets.items():
        if not data:
            print(f"\n{name}: No data found")
            continue

        print(f"\n{'='*40}")
        print(f"Processing: {name}")
        print(f"{'='*40}")
        print(f"Original count: {len(data)}")
        total_before += len(data)

        # Find duplicates
        unique, duplicates, dup_info = find_duplicates(data)
        print(f"After removing duplicates: {len(unique)} (removed {len(duplicates)})")

        # Find similar questions
        similar = find_similar_questions(unique)
        if similar:
            print(f"Found {len(similar)} similar question pairs")
            for (i, j), info in list(similar.items())[:3]:
                print(f"  - Similarity {info['similarity']:.2f}: '{info['q1']}...' vs '{info['q2']}...'")

        # Remove low quality
        high_quality, low_quality = remove_low_quality(unique)
        print(f"After quality filter: {len(high_quality)} (removed {len(low_quality)})")

        # Quality stats
        stats = evaluate_quality(high_quality)
        print(f"With thinking: {stats['has_thinking']} ({100*stats['has_thinking']/len(high_quality):.1f}%)")
        if stats['has_tool_call'] > 0:
            print(f"With tool calls: {stats['has_tool_call']}")
        print(f"Avg response length: {stats['avg_response_length']:.0f} chars")

        total_after += len(high_quality)

        # Add source tag
        for ex in high_quality:
            ex["_source"] = name
        all_examples.extend(high_quality)

    # Cross-dataset deduplication
    print(f"\n{'='*60}")
    print("Cross-Dataset Deduplication")
    print(f"{'='*60}")
    print(f"Total before cross-dedup: {len(all_examples)}")

    all_unique, all_dups, _ = find_duplicates(all_examples)
    print(f"Total after cross-dedup: {len(all_unique)} (removed {len(all_dups)})")

    # Final quality check
    print(f"\n{'='*60}")
    print("Final Quality Report")
    print(f"{'='*60}")

    final_stats = evaluate_quality(all_unique)
    print(f"Total examples: {final_stats['total']}")
    print(f"With thinking: {final_stats['has_thinking']} ({100*final_stats['has_thinking']/final_stats['total']:.1f}%)")
    print(f"With tool calls: {final_stats['has_tool_call']} ({100*final_stats['has_tool_call']/final_stats['total']:.1f}%)")
    print(f"Avg response length: {final_stats['avg_response_length']:.0f} chars")
    print(f"\nQuestion types:")
    for qtype, count in final_stats['question_types'].most_common():
        print(f"  {qtype}: {count} ({100*count/final_stats['total']:.1f}%)")

    if final_stats['tool_calls']:
        print(f"\nTool call distribution:")
        for tool, count in final_stats['tool_calls'].most_common(10):
            print(f"  {tool}: {count}")

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"Original total: {total_before}")
    print(f"Final total: {len(all_unique)}")
    print(f"Reduction: {total_before - len(all_unique)} ({100*(total_before - len(all_unique))/total_before:.1f}%)")

    return all_unique, final_stats


if __name__ == "__main__":
    deduplicate_and_clean_all()
