from abc import ABC, abstractmethod
from typing import Protocol

from .proxy_pool import Proxy


class BrowserClient(Protocol):
    """浏览器平台客户端协议"""

    def check_status(self) -> bool:
        """检查平台服务是否可用"""
        ...

    def start_browser(
        self, profile_id: str, headless: bool = False, **kwargs
    ) -> dict:
        """
        启动浏览器环境

        返回格式:
        {
            "ws": {"puppeteer": "ws://..."},
            "port": "12345",
            ...
        }
        """
        ...

    def stop_browser(self, profile_id: str) -> bool:
        """停止浏览器"""
        ...

    def update_profile_proxy(self, profile_id: str, proxy: Proxy) -> bool:
        """更新环境的代理配置"""
        ...

    def close(self):
        """关闭客户端"""
        ...


def get_browser_client() -> BrowserClient:
    """根据配置获取浏览器客户端"""
    from .config import config, BrowserPlatform

    if config.platform == BrowserPlatform.ADSPOWER:
        from .adspower_client import adspower
        return adspower
    elif config.platform == BrowserPlatform.MULTILOGINX:
        from .multiloginx_client import multiloginx
        return multiloginx
    else:
        raise ValueError(f"Unsupported browser platform: {config.platform}")
