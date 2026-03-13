"""示例任务"""

import asyncio
from playwright.async_api import Page, async_playwright

from src import register, BaseWorker


@register("check_ip")
class CheckIPTask(BaseWorker):
    """检查当前 IP"""

    async def run(self, page: Page):
        await page.goto("https://httpbin.org/ip", wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        content = await page.inner_text("body")
        print(f"[{self.account.name}] IP: {content}")
        return {"account": self.account.name, "ip": content}


@register("check_fingerprint")
class CheckFingerprintTask(BaseWorker):
    """检查浏览器指纹"""

    async def run(self, page: Page):
        await page.goto("https://browserleaks.com/canvas", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        title = await page.title()
        print(f"[{self.account.name}] Fingerprint: {title}")
        return {"title": title}


@register("web3_example")
class Web3ExampleTask(BaseWorker):
    """Web3 操作示例"""

    async def run(self, page: Page):
        wallet_address = self.account.web3.get("address")
        if not wallet_address:
            print(f"[{self.account.name}] No web3 wallet configured")
            return {"error": "no wallet"}

        print(f"[{self.account.name}] Wallet: {wallet_address}")
        await page.goto("https://etherscan.io", wait_until="domcontentloaded")
        return {"wallet": wallet_address}


@register("discord_example")
class DiscordExampleTask(BaseWorker):
    """Discord 操作示例"""

    async def run(self, page: Page):
        token = self.account.discord.get("token")
        if not token:
            print(f"[{self.account.name}] No discord token configured")
            return {"error": "no discord"}

        username = self.account.discord.get("username")
        print(f"[{self.account.name}] Discord: {username}")
        await page.goto("https://discord.com", wait_until="domcontentloaded")
        return {"discord_user": username}


# ========== 开发调试入口 ==========
# 直接用 Playwright 启动浏览器测试任务，不需要 AdsPower

async def dev_run():
    """
    开发模式：直接启动 Playwright 浏览器测试任务

    运行方式:
        uv run python tasks/examples.py
    """
    from dataclasses import dataclass, field
    from src import Account

    # 模拟账号数据
    mock_account = Account(
        name="dev_account",
        profile_id="dev_profile",
        web3={"address": "0x123...", "private_key": "xxx"},
        discord={"username": "dev#1234", "token": "xxx"},
    )

    # 启动浏览器
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 选择要测试的任务
        task = CheckIPTask("dev_profile", mock_account)

        try:
            print("=" * 50)
            print("开发模式: 测试任务逻辑")
            print("=" * 50)

            await task.on_start(page)
            result = await task.run(page)
            await task.on_finish(page, result)

            print("\n结果:", result)
            print("\n浏览器将在 10 秒后关闭...")
            await page.wait_for_timeout(10000)

        except Exception as e:
            print(f"错误: {e}")
            await task.on_error(page, e)

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(dev_run())
