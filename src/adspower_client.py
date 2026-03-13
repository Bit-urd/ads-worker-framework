import httpx

from .config import config
from .proxy_pool import Proxy


class AdsPowerError(Exception):
    pass


class AdsPowerClient:
    def __init__(self, api_url: str | None = None, api_key: str | None = None):
        self.api_url = (api_url or config.adspower.url).rstrip("/")
        self.api_key = api_key or config.adspower.api_key
        self.client = httpx.Client(timeout=config.request_timeout)

    def _get_headers(self) -> dict:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.api_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self._get_headers())
        resp = self.client.request(method, url, headers=headers, **kwargs)
        data = resp.json()
        if data.get("code") != 0:
            raise AdsPowerError(f"API error: {data.get('msg', 'Unknown error')}")
        return data

    def check_status(self) -> bool:
        try:
            data = self._request("GET", "/status")
            return data.get("code") == 0
        except Exception:
            return False

    def list_profiles(self, page: int = 1, page_size: int = 100) -> list[dict]:
        data = self._request(
            "GET",
            "/api/v1/user/list",
            params={"page": page, "page_size": page_size},
        )
        return data.get("data", {}).get("list", [])

    def start_browser(
        self, profile_id: str, headless: bool = False, ip_tab: bool = False
    ) -> dict:
        """启动浏览器环境"""
        params = {
            "user_id": profile_id,
            "headless": "1" if headless else "0",
            "ip_tab": "1" if ip_tab else "0",
        }
        data = self._request("GET", "/api/v1/browser/start", params=params)
        return data.get("data", {})

    def stop_browser(self, profile_id: str) -> bool:
        try:
            self._request(
                "GET", "/api/v1/browser/stop", params={"user_id": profile_id}
            )
            return True
        except AdsPowerError:
            return False

    def update_profile_proxy(self, profile_id: str, proxy: Proxy) -> bool:
        """更新环境的代理配置"""
        try:
            self._request(
                "POST",
                "/api/v1/user/update",
                json={
                    "user_id": profile_id,
                    "user_proxy_config": proxy.to_adspower_config(),
                },
            )
            return True
        except AdsPowerError:
            return False

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


adspower = AdsPowerClient()
