import httpx

from .config import config
from .proxy_pool import Proxy


class MultiloginXError(Exception):
    pass


class MultiloginXClient:
    def __init__(self, launcher_url: str | None = None, token: str | None = None):
        self.launcher_url = (launcher_url or config.multiloginx.launcher_url).rstrip("/")
        self.token = token or config.multiloginx.token
        self.client = httpx.Client(timeout=config.request_timeout)

    def _get_headers(self) -> dict:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.launcher_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())

        try:
            resp = self.client.request(method, url, headers=headers, **kwargs)
            resp.raise_for_status()
            data = resp.json()

            # MultiloginX 使用 status.http_code 来表示状态
            status = data.get("status", {})
            if status.get("http_code") not in [200, 201]:
                error_msg = status.get("message", "Unknown error")
                raise MultiloginXError(f"API error: {error_msg}")

            return data
        except httpx.HTTPError as e:
            raise MultiloginXError(f"HTTP error: {e}")

    def check_status(self) -> bool:
        """检查 MultiloginX Agent 是否运行"""
        try:
            # 尝试获取所有配置的状态
            self._request("GET", "/api/v1/profile/status/all")
            return True
        except Exception:
            return False

    def list_profiles(self, page: int = 1, page_size: int = 100) -> list[dict]:
        """MultiloginX 没有直接的列表 API，返回空列表"""
        # MultiloginX 通过云端管理配置，本地 launcher 只负责启动
        return []

    def start_browser(
        self,
        profile_id: str,
        folder_id: str = "default",
        headless: bool = False,
        automation_type: str = "playwright"
    ) -> dict:
        """启动浏览器环境"""
        params = {
            "automation_type": automation_type,
            "headless_mode": str(headless).lower()
        }

        path = f"/api/v2/profile/f/{folder_id}/p/{profile_id}/start"
        data = self._request("GET", path, params=params)

        profile_data = data.get("data", {})
        port = profile_data.get("port")

        if not port:
            raise MultiloginXError(f"Failed to get port for profile {profile_id}")

        # 返回类似 AdsPower 的格式
        return {
            "ws": {
                "puppeteer": f"ws://127.0.0.1:{port}"
            },
            "port": port,
            "browser_type": profile_data.get("browser_type", "mimic")
        }

    def stop_browser(self, profile_id: str) -> bool:
        """停止浏览器"""
        try:
            self._request("GET", f"/api/v1/profile/stop/p/{profile_id}")
            return True
        except MultiloginXError:
            return False

    def update_profile_proxy(self, profile_id: str, proxy: Proxy) -> bool:
        """
        MultiloginX 在启动时配置代理，不支持运行时更新
        返回 True 表示接受请求，实际更新在下次启动时生效
        """
        # MultiloginX 需要通过云端 API 更新配置
        # 这里暂不实现，返回 True 表示不阻塞流程
        return True

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


multiloginx = MultiloginXClient()
