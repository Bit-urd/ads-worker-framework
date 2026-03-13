import asyncio
from dataclasses import dataclass
from typing import Any, Type

from .account_manager import account_manager, Account
from .browser_manager import browser_manager
from .config import config
from .logger import get_logger
from .worker import BaseWorker

log = get_logger("runner")


@dataclass
class TaskResult:
    profile_id: str
    task_name: str
    account_name: str | None
    success: bool
    result: Any = None
    error: str | None = None


async def run_single_worker(
    worker_class: Type[BaseWorker],
    task_name: str,
    profile_id: str,
    semaphore: asyncio.Semaphore,
) -> TaskResult:
    """运行单个 Worker"""
    async with semaphore:
        session = None
        account: Account | None = None

        try:
            # 获取账号
            account = await account_manager.acquire(profile_id)
            if not account:
                log.warning(f"[{profile_id}] No account available")
                return TaskResult(
                    profile_id=profile_id,
                    task_name=task_name,
                    account_name=None,
                    success=False,
                    error=f"No account available for profile {profile_id}",
                )

            log.info(f"[{profile_id}] Starting task '{task_name}' with account '{account.name}'")

            session = await browser_manager.get_browser(
                profile_id=profile_id,
                proxy=account.proxy,
            )

            worker = worker_class(profile_id, account)

            await worker.on_start(session.page)
            result = await worker.run(session.page)
            await worker.on_finish(session.page, result)

            log.info(f"[{profile_id}] Task '{task_name}' completed successfully")

            return TaskResult(
                profile_id=profile_id,
                task_name=task_name,
                account_name=account.name,
                success=True,
                result=result,
            )

        except Exception as e:
            log.error(f"[{profile_id}] Task '{task_name}' failed: {e}")

            if session and account:
                worker = worker_class(profile_id, account)
                await worker.on_error(session.page, e)

            return TaskResult(
                profile_id=profile_id,
                task_name=task_name,
                account_name=account.name if account else None,
                success=False,
                error=str(e),
            )

        finally:
            if session:
                await browser_manager.close_browser(profile_id)
            await account_manager.release(profile_id)


async def run_task(
    worker_class: Type[BaseWorker],
    task_name: str,
    profile_ids: list[str],
    concurrency: int | None = None,
) -> list[TaskResult]:
    """运行单个任务（在多个 profile 上）"""
    concurrency = concurrency or config.concurrency
    semaphore = asyncio.Semaphore(concurrency)

    log.info(f"Running task '{task_name}' on {len(profile_ids)} profiles (concurrency={concurrency})")

    tasks = [
        run_single_worker(worker_class, task_name, pid, semaphore)
        for pid in profile_ids
    ]

    results = await asyncio.gather(*tasks)
    return list(results)


async def run_tasks(
    task_configs: list[dict],
    concurrency: int | None = None,
) -> dict[str, list[TaskResult]]:
    """运行多个任务"""
    concurrency = concurrency or config.concurrency
    semaphore = asyncio.Semaphore(concurrency)

    task_names = [cfg["task_name"] for cfg in task_configs]
    log.info(f"Running tasks {task_names} (concurrency={concurrency})")

    all_tasks = []
    task_indices = {}

    idx = 0
    for cfg in task_configs:
        worker_class = cfg["worker_class"]
        task_name = cfg["task_name"]
        profile_ids = cfg["profile_ids"]

        start_idx = idx
        for pid in profile_ids:
            all_tasks.append(
                run_single_worker(worker_class, task_name, pid, semaphore)
            )
            idx += 1
        task_indices[task_name] = (start_idx, idx)

    all_results = await asyncio.gather(*all_tasks)

    grouped_results = {}
    for task_name, (start, end) in task_indices.items():
        grouped_results[task_name] = list(all_results[start:end])

    # 统计结果
    for task_name, results in grouped_results.items():
        success = sum(1 for r in results if r.success)
        failed = len(results) - success
        log.info(f"Task '{task_name}' finished: {success} success, {failed} failed")

    return grouped_results
