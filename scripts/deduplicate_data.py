#!/usr/bin/env python3
"""
データセットの重複・類似プロンプト検出・除去スクリプト
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher
import hashlib
import argparse
from typing import Dict, List, Tuple, Set


def extract_user_prompt(entry: dict) -> str:
    """messagesからユーザープロンプトを抽出"""
    messages = entry.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def normalize_text(text: str) -> str:
    """テキストを正規化（比較用）"""
    # 空白・改行を統一
    text = " ".join(text.split())
    # 小文字化（英字のみ）
    return text.lower()


def calculate_similarity(text1: str, text2: str) -> float:
    """2つのテキストの類似度を計算（0-1）"""
    return SequenceMatcher(None, text1, text2).ratio()


def get_text_hash(text: str) -> str:
    """テキストのハッシュを取得"""
    normalized = normalize_text(text)
    return hashlib.md5(normalized.encode()).hexdigest()


def load_all_data(data_dir: str) -> Dict[str, List[Tuple[int, dict, str]]]:
    """全JSONLファイルを読み込み、ファイルごとにデータを返す"""
    data_by_file = {}
    data_dir = Path(data_dir)

    for jsonl_file in sorted(data_dir.glob("*.jsonl")):
        entries = []
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    prompt = extract_user_prompt(entry)
                    entries.append((idx, entry, prompt))
                except json.JSONDecodeError:
                    print(f"警告: {jsonl_file}の{idx}行目がパースできません")

        data_by_file[jsonl_file.name] = entries
        print(f"読み込み: {jsonl_file.name} ({len(entries)}件)")

    return data_by_file


def find_exact_duplicates(data_by_file: Dict[str, List[Tuple[int, dict, str]]]) -> Dict[str, List[Tuple[str, int, str]]]:
    """完全一致の重複を検出"""
    # プロンプトのハッシュ -> [(ファイル名, 行番号, プロンプト), ...]
    hash_to_entries = defaultdict(list)

    for filename, entries in data_by_file.items():
        for idx, entry, prompt in entries:
            if prompt:
                h = get_text_hash(prompt)
                hash_to_entries[h].append((filename, idx, prompt))

    # 2件以上あるものが重複
    duplicates = {h: entries for h, entries in hash_to_entries.items() if len(entries) > 1}
    return duplicates


def find_similar_prompts(
    data_by_file: Dict[str, List[Tuple[int, dict, str]]],
    threshold: float = 0.85,
    sample_size: int = 5000
) -> List[Tuple[float, Tuple[str, int, str], Tuple[str, int, str]]]:
    """類似プロンプトを検出（しきい値以上の類似度）"""
    # 全プロンプトをフラットに
    all_prompts = []
    for filename, entries in data_by_file.items():
        for idx, entry, prompt in entries:
            if prompt and len(prompt) > 10:  # 短すぎるプロンプトは除外
                all_prompts.append((filename, idx, prompt, normalize_text(prompt)))

    print(f"類似度チェック対象: {len(all_prompts)}件")

    # サンプリング（全件比較は O(n^2) で重い）
    if len(all_prompts) > sample_size:
        import random
        random.seed(42)
        sampled = random.sample(all_prompts, sample_size)
        print(f"サンプリング: {sample_size}件に限定")
    else:
        sampled = all_prompts

    similar_pairs = []
    checked = set()

    total = len(sampled)
    for i, (file1, idx1, prompt1, norm1) in enumerate(sampled):
        if i % 500 == 0:
            print(f"  進捗: {i}/{total}")

        for j, (file2, idx2, prompt2, norm2) in enumerate(sampled[i+1:], start=i+1):
            # 同じファイル内の近い行は同じデータの可能性が高いのでスキップ
            if file1 == file2 and abs(idx1 - idx2) < 3:
                continue

            # 長さが大きく異なるものはスキップ（高速化）
            len_ratio = min(len(norm1), len(norm2)) / max(len(norm1), len(norm2))
            if len_ratio < 0.5:
                continue

            sim = calculate_similarity(norm1, norm2)
            if sim >= threshold:
                similar_pairs.append((
                    sim,
                    (file1, idx1, prompt1),
                    (file2, idx2, prompt2)
                ))

    # 類似度順にソート
    similar_pairs.sort(key=lambda x: -x[0])
    return similar_pairs


def create_deduplicated_data(
    data_by_file: Dict[str, List[Tuple[int, dict, str]]],
    exact_duplicates: Dict[str, List[Tuple[str, int, str]]],
    similar_pairs: List[Tuple[float, Tuple[str, int, str], Tuple[str, int, str]]],
    output_dir: str
) -> Dict[str, int]:
    """重複・類似を除去したデータを作成"""
    # 除外するエントリを特定（ファイル名, 行番号）
    to_exclude: Set[Tuple[str, int]] = set()

    # 完全一致重複: 最初の1件以外を除外
    for h, entries in exact_duplicates.items():
        for filename, idx, prompt in entries[1:]:  # 最初を残す
            to_exclude.add((filename, idx))

    # 類似ペア: 後のものを除外
    for sim, (file1, idx1, _), (file2, idx2, _) in similar_pairs:
        # file2, idx2を除外（ペアの後者）
        to_exclude.add((file2, idx2))

    print(f"除外対象: {len(to_exclude)}件")

    # 出力
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {}
    for filename, entries in data_by_file.items():
        original_count = len(entries)
        kept_entries = [
            entry for idx, entry, prompt in entries
            if (filename, idx) not in to_exclude
        ]

        output_path = output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            for entry in kept_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        removed = original_count - len(kept_entries)
        stats[filename] = {"original": original_count, "kept": len(kept_entries), "removed": removed}
        if removed > 0:
            print(f"  {filename}: {original_count} -> {len(kept_entries)} (-{removed})")

    return stats


def main():
    parser = argparse.ArgumentParser(description="データセットの重複・類似除去")
    parser.add_argument("--data-dir", default="data", help="データディレクトリ")
    parser.add_argument("--output-dir", default="data_dedup", help="出力ディレクトリ")
    parser.add_argument("--similarity-threshold", type=float, default=0.85, help="類似度しきい値 (0-1)")
    parser.add_argument("--report-only", action="store_true", help="レポートのみ（ファイル出力なし）")
    args = parser.parse_args()

    print("=" * 60)
    print("データセット重複・類似チェック")
    print("=" * 60)

    # データ読み込み
    data_by_file = load_all_data(args.data_dir)
    total_entries = sum(len(entries) for entries in data_by_file.values())
    print(f"\n合計: {total_entries}件")

    # 完全一致重複検出
    print("\n" + "-" * 40)
    print("1. 完全一致の重複を検出中...")
    exact_duplicates = find_exact_duplicates(data_by_file)

    if exact_duplicates:
        print(f"\n完全一致の重複グループ: {len(exact_duplicates)}件")
        for h, entries in list(exact_duplicates.items())[:10]:  # 最初の10件を表示
            print(f"\n  重複グループ ({len(entries)}件):")
            for filename, idx, prompt in entries:
                short_prompt = prompt[:60].replace("\n", " ") + ("..." if len(prompt) > 60 else "")
                print(f"    - {filename}:{idx+1} | {short_prompt}")
        if len(exact_duplicates) > 10:
            print(f"\n  ... 他 {len(exact_duplicates) - 10}件の重複グループ")
    else:
        print("完全一致の重複はありません")

    # 類似プロンプト検出
    print("\n" + "-" * 40)
    print(f"2. 類似プロンプトを検出中 (しきい値: {args.similarity_threshold})...")
    similar_pairs = find_similar_prompts(data_by_file, threshold=args.similarity_threshold)

    if similar_pairs:
        print(f"\n類似ペア: {len(similar_pairs)}件")
        for sim, (file1, idx1, prompt1), (file2, idx2, prompt2) in similar_pairs[:15]:  # 最初の15件
            print(f"\n  類似度: {sim:.2%}")
            short1 = prompt1[:50].replace("\n", " ") + ("..." if len(prompt1) > 50 else "")
            short2 = prompt2[:50].replace("\n", " ") + ("..." if len(prompt2) > 50 else "")
            print(f"    A: {file1}:{idx1+1} | {short1}")
            print(f"    B: {file2}:{idx2+1} | {short2}")
        if len(similar_pairs) > 15:
            print(f"\n  ... 他 {len(similar_pairs) - 15}件の類似ペア")
    else:
        print("類似プロンプトはありません")

    # 重複除去したデータを出力
    if not args.report_only:
        print("\n" + "-" * 40)
        print("3. 重複除去したデータを出力中...")
        stats = create_deduplicated_data(
            data_by_file, exact_duplicates, similar_pairs, args.output_dir
        )

        total_removed = sum(s["removed"] for s in stats.values())
        total_kept = sum(s["kept"] for s in stats.values())
        print(f"\n完了: {total_entries} -> {total_kept} (-{total_removed}件)")
        print(f"出力先: {args.output_dir}/")

    # サマリー
    print("\n" + "=" * 60)
    print("サマリー")
    print("=" * 60)
    dup_count = sum(len(entries) - 1 for entries in exact_duplicates.values())
    print(f"完全一致の重複: {dup_count}件")
    print(f"類似プロンプト: {len(similar_pairs)}件")


if __name__ == "__main__":
    main()
