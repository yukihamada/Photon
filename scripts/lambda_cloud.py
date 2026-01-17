#!/usr/bin/env python3
"""
Lambda Labs Cloud API操作スクリプト

インスタンスの起動・停止・状態確認を行う
"""

import os
import argparse
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv(Path(__file__).parent.parent / '.env')

LAMBDA_API_BASE = "https://cloud.lambdalabs.com/api/v1"


def get_api_key():
    """APIキーを取得"""
    api_key = os.getenv("LAMBDA_API_KEY")
    if not api_key:
        raise ValueError("LAMBDA_API_KEY が設定されていません。.envファイルを確認してください。")
    return api_key


def get_headers():
    """APIリクエスト用ヘッダー"""
    return {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }


def list_instance_types():
    """利用可能なインスタンスタイプを一覧表示"""
    response = requests.get(
        f"{LAMBDA_API_BASE}/instance-types",
        headers=get_headers()
    )
    response.raise_for_status()
    data = response.json()

    print("\n=== 利用可能なインスタンスタイプ ===\n")
    for name, info in data.get("data", {}).items():
        desc = info.get("instance_type", {})
        price = desc.get("price_cents_per_hour", 0) / 100
        specs = desc.get("specs", {})

        regions = [r.get("name", "N/A") for r in info.get("regions_with_capacity_available", [])]

        print(f"【{name}】")
        print(f"  GPU: {specs.get('gpus', 'N/A')}")
        print(f"  vCPU: {specs.get('vcpus', 'N/A')}")
        print(f"  RAM: {specs.get('memory_gib', 'N/A')} GB")
        print(f"  Storage: {specs.get('storage_gib', 'N/A')} GB")
        print(f"  価格: ${price:.2f}/時間")
        print(f"  利用可能リージョン: {', '.join(regions) if regions else '現在利用不可'}")
        print()

    return data


def list_instances():
    """起動中のインスタンスを一覧表示"""
    response = requests.get(
        f"{LAMBDA_API_BASE}/instances",
        headers=get_headers()
    )
    response.raise_for_status()
    data = response.json()

    instances = data.get("data", [])

    if not instances:
        print("\n起動中のインスタンスはありません。")
        return data

    print("\n=== 起動中のインスタンス ===\n")
    for inst in instances:
        print(f"【{inst.get('name', 'N/A')}】")
        print(f"  ID: {inst.get('id')}")
        print(f"  タイプ: {inst.get('instance_type', {}).get('name', 'N/A')}")
        print(f"  ステータス: {inst.get('status')}")
        print(f"  IP: {inst.get('ip', 'N/A')}")
        print(f"  リージョン: {inst.get('region', {}).get('name', 'N/A')}")
        print()

    return data


def launch_instance(
    instance_type: str = "gpu_1x_a100",
    region: str = "us-east-1",
    name: str = "eliochat-training",
    ssh_key_names: list = None,
):
    """インスタンスを起動"""
    payload = {
        "region_name": region,
        "instance_type_name": instance_type,
        "name": name,
    }

    if ssh_key_names:
        payload["ssh_key_names"] = ssh_key_names

    print(f"\nインスタンスを起動中...")
    print(f"  タイプ: {instance_type}")
    print(f"  リージョン: {region}")
    print(f"  名前: {name}")

    response = requests.post(
        f"{LAMBDA_API_BASE}/instance-operations/launch",
        headers=get_headers(),
        json=payload
    )

    if response.status_code != 200:
        print(f"\nエラー: {response.status_code}")
        print(response.json())
        return None

    data = response.json()
    instance_ids = data.get("data", {}).get("instance_ids", [])

    if instance_ids:
        print(f"\n起動成功！")
        print(f"インスタンスID: {instance_ids[0]}")
        print("\n数分後に 'python lambda_cloud.py list' でIPアドレスを確認してください。")

    return data


def terminate_instance(instance_id: str):
    """インスタンスを終了"""
    print(f"\nインスタンスを終了中: {instance_id}")

    response = requests.post(
        f"{LAMBDA_API_BASE}/instance-operations/terminate",
        headers=get_headers(),
        json={"instance_ids": [instance_id]}
    )

    if response.status_code == 200:
        print("終了リクエストを送信しました。")
    else:
        print(f"エラー: {response.status_code}")
        print(response.json())

    return response.json()


def list_ssh_keys():
    """登録済みSSHキーを一覧表示"""
    response = requests.get(
        f"{LAMBDA_API_BASE}/ssh-keys",
        headers=get_headers()
    )
    response.raise_for_status()
    data = response.json()

    keys = data.get("data", [])

    if not keys:
        print("\n登録されているSSHキーはありません。")
        print("Lambda Labsダッシュボードでキーを追加してください。")
        return data

    print("\n=== 登録済みSSHキー ===\n")
    for key in keys:
        print(f"  - {key.get('name')}")

    return data


def main():
    parser = argparse.ArgumentParser(description='Lambda Labs Cloud操作')
    subparsers = parser.add_subparsers(dest='command', help='コマンド')

    # list コマンド
    subparsers.add_parser('list', help='起動中のインスタンスを表示')

    # types コマンド
    subparsers.add_parser('types', help='利用可能なインスタンスタイプを表示')

    # keys コマンド
    subparsers.add_parser('keys', help='登録済みSSHキーを表示')

    # launch コマンド
    launch_parser = subparsers.add_parser('launch', help='インスタンスを起動')
    launch_parser.add_argument('--type', type=str, default='gpu_1x_a100',
                               help='インスタンスタイプ (default: gpu_1x_a100)')
    launch_parser.add_argument('--region', type=str, default='us-east-1',
                               help='リージョン (default: us-east-1)')
    launch_parser.add_argument('--name', type=str, default='eliochat-training',
                               help='インスタンス名')
    launch_parser.add_argument('--ssh-key', type=str, action='append',
                               help='使用するSSHキー名')

    # terminate コマンド
    term_parser = subparsers.add_parser('terminate', help='インスタンスを終了')
    term_parser.add_argument('instance_id', type=str, help='終了するインスタンスID')

    args = parser.parse_args()

    if args.command == 'list':
        list_instances()
    elif args.command == 'types':
        list_instance_types()
    elif args.command == 'keys':
        list_ssh_keys()
    elif args.command == 'launch':
        ssh_keys = args.ssh_key if args.ssh_key else None
        launch_instance(args.type, args.region, args.name, ssh_keys)
    elif args.command == 'terminate':
        terminate_instance(args.instance_id)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
