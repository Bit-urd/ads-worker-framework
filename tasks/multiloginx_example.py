"""
使用 MultiloginX 的示例任务

演示如何在配置中选择 MultiloginX 平台并执行任务
"""

import asyncio
from src import BaseWorker, register, browser_manager


@register("multiloginx_example")
class MultiloginXExampleWorker(BaseWorker):
    """MultiloginX 示例任务"""

    async def run(self):
        """执行任务"""
        self.logger.info(f"开始执行任务，使用账号: {self.account.name}")

        # 获取浏览器会话
        session = await browser_manager.get_browser(
            profile_id=self.account.profile_id,
            headless=False,
        )

        try:
            page = session.page

            # 访问网页
            self.logger.info("访问 Multilogin 官网")
            await page.goto("https://multilogin.com")

            # 获取标题
            title = await page.title()
            self.logger.info(f"页面标题: {title}")

            # 等待一段时间
            await asyncio.sleep(3)

            self.logger.info("任务执行成功")
            return {"status": "success", "title": title}

        except Exception as e:
            self.logger.error(f"任务执行失败: {e}")
            return {"status": "error", "message": str(e)}

        finally:
            # 关闭浏览器
            await browser_manager.close_browser(self.account.profile_id)


if __name__ == "__main__":
    """
    使用方法：

    1. 在 config/accounts.yaml 中配置：
       platform: multiloginx
       multiloginx:
         launcher_url: https://launcher.mlx.yt:45001
         token: "your-token"
         folder_id: "your-folder-id"

       accounts:
         - name: test_account
           profile_id: "your-profile-id"

    2. 运行任务：
       python tasks/multiloginx_example.py
    """
    from src import run_task

    result = asyncio.run(run_task("multiloginx_example", "test_account"))
    print(f"\n任务结果: {result}")
