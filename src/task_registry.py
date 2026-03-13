"""任务注册系统"""

from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from .worker import BaseWorker


class TaskRegistry:
    """任务注册表"""

    _tasks: dict[str, Type["BaseWorker"]] = {}

    @classmethod
    def register(cls, name: str):
        """
        装饰器：注册任务

        使用方式:
            @register("my_task")
            class MyTask(BaseWorker):
                async def run(self, page):
                    ...
        """
        def decorator(worker_class):
            cls._tasks[name] = worker_class
            return worker_class
        return decorator

    @classmethod
    def get(cls, name: str):
        """获取任务类"""
        return cls._tasks.get(name)

    @classmethod
    def list_tasks(cls) -> list[str]:
        """列出所有已注册的任务名"""
        return list(cls._tasks.keys())

    @classmethod
    def all(cls) -> dict:
        """获取所有任务"""
        return cls._tasks.copy()


register = TaskRegistry.register
