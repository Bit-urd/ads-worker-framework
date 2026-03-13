from abc import ABC, abstractmethod
from typing import Any

from playwright.async_api import Page

from .account_manager import Account


class BaseWorker(ABC):
    """
    Worker 基类

    用户需要继承此类并实现 run 方法来编写自动化业务逻辑。
    可以通过 self.account 访问账号的所有配置信息。

    示例:
        @register("my_task")
        class MyTask(BaseWorker):
            async def run(self, page: Page) -> Any:
                wallet = self.account.web3.get("private_key")
                discord_token = self.account.discord.get("token")
                await page.goto("https://example.com")
                return {"done": True}
    """

    def __init__(self, profile_id: str, account: Account):
        self.profile_id = profile_id
        self.account = account

    @abstractmethod
    async def run(self, page: Page) -> Any:
        """执行自动化任务"""
        raise NotImplementedError

    async def on_start(self, page: Page) -> None:
        """任务开始前的钩子"""
        pass

    async def on_finish(self, page: Page, result: Any) -> None:
        """任务完成后的钩子"""
        pass

    async def on_error(self, page: Page, error: Exception) -> None:
        """任务出错时的钩子"""
        pass
