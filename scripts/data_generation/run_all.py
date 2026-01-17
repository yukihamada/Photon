#!/usr/bin/env python3
"""
Master script to run all data generation
Usage: python run_all.py [--skip-api] [--verify-only]
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="Generate ElioChat training data")
    parser.add_argument("--skip-api", action="store_true",
                       help="Skip API-based generation (logic/reasoning)")
    parser.add_argument("--verify-only", action="store_true",
                       help="Only verify existing data")
    parser.add_argument("--logic-only", action="store_true",
                       help="Only generate logic/math data")
    parser.add_argument("--reasoning-only", action="store_true",
                       help="Only generate reasoning data")
    parser.add_argument("--tool-only", action="store_true",
                       help="Only generate tool calling data")
    parser.add_argument("--anti-hallucination-only", action="store_true",
                       help="Only generate anti-hallucination data")
    parser.add_argument("--count", type=int, default=None,
                       help="Override target count for generation")
    args = parser.parse_args()

    if args.verify_only:
        print("Running verification only...")
        from verify_data import verify_all_datasets
        verify_all_datasets()
        return

    # Import generators
    from config import DATA_CONFIG

    if args.logic_only or (not args.skip_api and not any([
        args.reasoning_only, args.tool_only, args.anti_hallucination_only
    ])):
        print("\n" + "="*60)
        print("Generating Logic/Math Data")
        print("="*60)
        from generate_logic_data import generate_logic_dataset
        count = args.count or DATA_CONFIG["logic_math"]["count"]
        asyncio.run(generate_logic_dataset(count))

    if args.reasoning_only or (not args.skip_api and not any([
        args.logic_only, args.tool_only, args.anti_hallucination_only
    ])):
        print("\n" + "="*60)
        print("Generating Reasoning Data")
        print("="*60)
        from generate_reasoning_data import generate_reasoning_dataset
        count = args.count or DATA_CONFIG["reasoning"]["count"]
        asyncio.run(generate_reasoning_dataset(count))

    if args.tool_only or not any([
        args.logic_only, args.reasoning_only, args.anti_hallucination_only
    ]):
        print("\n" + "="*60)
        print("Generating Tool Calling Data")
        print("="*60)
        from generate_tool_data import generate_tool_dataset
        count = args.count or DATA_CONFIG["tool_calling"]["count"]
        generate_tool_dataset(count)

    if args.anti_hallucination_only or not any([
        args.logic_only, args.reasoning_only, args.tool_only
    ]):
        print("\n" + "="*60)
        print("Generating Anti-Hallucination Data")
        print("="*60)
        from generate_anti_hallucination import generate_anti_hallucination_dataset
        count = args.count or DATA_CONFIG["anti_hallucination"]["count"]
        generate_anti_hallucination_dataset(count)

    # Verify all data
    print("\n" + "="*60)
    print("Verifying Generated Data")
    print("="*60)
    from verify_data import verify_all_datasets
    verify_all_datasets()

    # Merge datasets
    print("\n" + "="*60)
    print("Merging Datasets")
    print("="*60)
    from merge_datasets import merge_datasets
    merge_datasets()

    print("\n" + "="*60)
    print("DATA GENERATION COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
