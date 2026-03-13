#!/usr/bin/env python3
"""
任务运行入口

使用方式:
    uv run python main.py --list           # 列出所有任务
    uv run python main.py --accounts       # 列出所有账号
    uv run python main.py -t check_ip      # 运行单个任务
    uv run python main.py -t check_ip -t web3_example  # 运行多个任务
    uv run python main.py -t check_ip -p p1,p2,p3      # 指定 profiles
    uv run python main.py -t check_ip -c 5             # 指定并发数
"""

import argparse
import asyncio

from src import adspower, account_manager, config, TaskRegistry, run_tasks
from src.config import AllocationMode

# 导入 tasks 模块以注册所有任务
import tasks  # noqa: F401


def parse_args():
    parser = argparse.ArgumentParser(description="AdsPower Worker Framework")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有任务")
    parser.add_argument("--accounts", "-a", action="store_true", help="列出所有账号")
    parser.add_argument("--task", "-t", action="append", dest="tasks", help="任务名")
    parser.add_argument("--profiles", "-p", type=str, help="Profile IDs (逗号分隔)")
    parser.add_argument("--concurrency", "-c", type=int, default=None, help="并发数")
    return parser.parse_args()


def show_accounts():
    accounts = account_manager.list_accounts()
    mode = "固定绑定" if config.mode == AllocationMode.FIXED else "账号池"

    print(f"模式: {mode}")
    print(f"账号总数: {len(accounts)}\n")

    for acc in accounts:
        print(f"  {acc.name}")
        if acc.profile_id:
            print(f"    Profile: {acc.profile_id}")
        proxy_info = f"{acc.proxy.host}:{acc.proxy.port}" if acc.proxy else "无代理"
        print(f"    Proxy:   {proxy_info}")

        services = []
        if acc.web3.get("address"): services.append("web3")
        if acc.discord.get("token"): services.append("discord")
        if acc.telegram.get("session"): services.append("telegram")
        if acc.google.get("email"): services.append("google")
        if acc.twitter.get("token"): services.append("twitter")
        if services:
            print(f"    Services: {', '.join(services)}")
        print()


async def main():
    args = parse_args()

    if args.list:
        print("已注册的任务:")
        for name in TaskRegistry.list_tasks():
            worker_class = TaskRegistry.get(name)
            doc = (worker_class.__doc__ or "").strip()
            print(f"  - {name}: {doc}")
        return

    if args.accounts:
        show_accounts()
        return

    if not adspower.check_status():
        print("Error: AdsPower 未运行")
        return

    accounts = account_manager.list_accounts()
    if not accounts:
        print("Error: 没有配置账号，请编辑 config/accounts.yaml")
        return

    # 获取 profile IDs
    if args.profiles:
        profile_ids = [p.strip() for p in args.profiles.split(",")]
    elif config.mode == AllocationMode.FIXED:
        # fixed 模式：使用配置中的 profile_ids
        profile_ids = account_manager.list_profile_ids()
        if not profile_ids:
            print("Error: fixed 模式下账号需要配置 profile_id")
            return
    else:
        # pool 模式：从 AdsPower 获取 profiles
        profiles = adspower.list_profiles(page=1, page_size=100)
        if not profiles:
            print("Error: AdsPower 中没有 profile")
            return
        profile_ids = [p["user_id"] for p in profiles]

    if not args.tasks:
        print("Error: 请指定任务，使用 --task <name>")
        print("运行 --list 查看所有任务")
        return

    task_configs = []
    for task_name in args.tasks:
        worker_class = TaskRegistry.get(task_name)
        if not worker_class:
            print(f"Error: 未知任务 '{task_name}'")
            return
        task_configs.append({
            "worker_class": worker_class,
            "task_name": task_name,
            "profile_ids": profile_ids,
        })

    concurrency = args.concurrency or config.concurrency
    mode_str = "fixed" if config.mode == AllocationMode.FIXED else "pool"

    print(f"模式: {mode_str}")
    print(f"任务: {args.tasks}")
    print(f"Profiles: {len(profile_ids)} 个")
    print(f"账号: {len(accounts)} 个")
    print(f"并发: {concurrency}")
    print("-" * 40)

    results = await run_tasks(task_configs, concurrency=concurrency)

    print("\n" + "=" * 40)
    print("结果:")
    for task_name, task_results in results.items():
        print(f"\n[{task_name}]")
        for r in task_results:
            status = "OK" if r.success else "FAIL"
            account_info = f" ({r.account_name})" if r.account_name else ""
            print(f"  {r.profile_id}{account_info}: {status}")
            if r.error:
                print(f"    Error: {r.error}")


if __name__ == "__main__":
    asyncio.run(main())
