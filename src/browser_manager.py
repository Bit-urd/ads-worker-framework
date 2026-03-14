import asyncio
from dataclasses import dataclass

from playwright.async_api import Browser, Page, async_playwright

from .browser_platform import get_browser_client
from .config import config, BrowserPlatform
from .proxy_pool import Proxy


class BrowserError(Exception):
    """浏览器操作错误"""
    pass


@dataclass
class BrowserSession:
    profile_id: str
    browser: Browser
    page: Page
    ws_endpoint: str


class BrowserManager:
    def __init__(self):
        self._sessions: dict[str, BrowserSession] = {}
        self._playwright = None
        self._lock = asyncio.Lock()
        self._client = get_browser_client()

    async def _ensure_playwright(self):
        if self._playwright is None:
            self._playwright = await async_playwright().start()

    async def get_browser(
        self,
        profile_id: str,
        proxy: Proxy | None = None,
        headless: bool = False,
    ) -> BrowserSession:
        """获取浏览器会话"""
        async with self._lock:
            if profile_id in self._sessions:
                return self._sessions[profile_id]

        # 如果提供了代理，先更新环境配置
        if proxy:
            self._client.update_profile_proxy(profile_id, proxy)

        # 启动浏览器
        try:
            # MultiloginX 需要额外的参数
            if config.platform == BrowserPlatform.MULTILOGINX:
                browser_data = self._client.start_browser(
                    profile_id,
                    folder_id=config.multiloginx.folder_id,
                    headless=headless,
                    automation_type="playwright"
                )
            else:
                browser_data = self._client.start_browser(
                    profile_id,
                    headless=headless
                )
        except Exception as e:
            raise BrowserError(f"Failed to start browser for {profile_id}: {e}")

        ws_endpoint = browser_data.get("ws", {}).get("puppeteer")

        if not ws_endpoint:
            raise BrowserError(f"Failed to get WebSocket endpoint for {profile_id}")

        # 连接 Playwright
        await self._ensure_playwright()
        browser = await self._playwright.chromium.connect_over_cdp(ws_endpoint)

        # 获取或创建页面
        contexts = browser.contexts
        if contexts:
            pages = contexts[0].pages
            page = pages[0] if pages else await contexts[0].new_page()
        else:
            context = await browser.new_context()
            page = await context.new_page()

        session = BrowserSession(
            profile_id=profile_id,
            browser=browser,
            page=page,
            ws_endpoint=ws_endpoint,
        )

        async with self._lock:
            self._sessions[profile_id] = session

        return session

    async def close_browser(self, profile_id: str) -> None:
        async with self._lock:
            session = self._sessions.pop(profile_id, None)

        if session:
            try:
                await session.browser.close()
            except Exception:
                pass

        self._client.stop_browser(profile_id)

    async def close_all(self) -> None:
        profile_ids = list(self._sessions.keys())
        for profile_id in profile_ids:
            await self.close_browser(profile_id)

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


browser_manager = BrowserManager()
