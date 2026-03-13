"""账号管理器"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .config import config, AllocationMode
from .proxy_pool import Proxy


@dataclass
class Account:
    """账号配置"""
    name: str
    profile_id: str | None = None  # fixed 模式必填，pool 模式可选
    proxy: Proxy | None = None
    web3: dict = field(default_factory=dict)
    discord: dict = field(default_factory=dict)
    telegram: dict = field(default_factory=dict)
    google: dict = field(default_factory=dict)
    twitter: dict = field(default_factory=dict)
    custom: dict = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """获取任意属性"""
        return getattr(self, key, self.custom.get(key, default))


class AccountManager:
    """账号管理器"""

    def __init__(self, accounts_file: Path | None = None):
        self.accounts_file = accounts_file or config.accounts_file
        self.mode = config.mode
        self.accounts: list[Account] = []
        self._profile_map: dict[str, Account] = {}  # profile_id -> account
        self._pool_in_use: dict[str, Account] = {}  # profile_id -> account (pool 模式)
        self._pool_lock = asyncio.Lock()
        self._load()

    def _load(self) -> None:
        """从 YAML 加载账号配置"""
        if not self.accounts_file.exists():
            return

        with open(self.accounts_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for item in data.get("accounts", []):
            proxy = None
            if "proxy" in item and item["proxy"]:
                p = item["proxy"]
                proxy = Proxy(
                    host=p.get("host", ""),
                    port=int(p.get("port", 0)),
                    username=p.get("username", ""),
                    password=p.get("password", ""),
                )

            profile_id = item.get("profile_id")

            account = Account(
                name=item.get("name", ""),
                profile_id=profile_id,
                proxy=proxy,
                web3=item.get("web3", {}),
                discord=item.get("discord", {}),
                telegram=item.get("telegram", {}),
                google=item.get("google", {}),
                twitter=item.get("twitter", {}),
                custom=item.get("custom", {}),
            )
            self.accounts.append(account)

            # fixed 模式下建立 profile_id 映射
            if profile_id:
                self._profile_map[profile_id] = account

    def get_by_name(self, name: str) -> Account | None:
        """按名称获取账号"""
        for account in self.accounts:
            if account.name == name:
                return account
        return None

    def get_by_profile(self, profile_id: str) -> Account | None:
        """按 profile ID 获取账号 (fixed 模式)"""
        return self._profile_map.get(profile_id)

    async def acquire(self, profile_id: str) -> Account | None:
        """
        获取账号

        - fixed 模式：返回绑定的账号
        - pool 模式：从池中分配一个未使用的账号
        """
        if self.mode == AllocationMode.FIXED:
            return self.get_by_profile(profile_id)

        # pool 模式
        async with self._pool_lock:
            # 已分配给此 profile
            if profile_id in self._pool_in_use:
                return self._pool_in_use[profile_id]

            # 找一个未使用的账号
            in_use_names = {a.name for a in self._pool_in_use.values()}
            for account in self.accounts:
                if account.name not in in_use_names:
                    self._pool_in_use[profile_id] = account
                    return account

            return None

    async def release(self, profile_id: str) -> None:
        """
        释放账号 (pool 模式)

        - fixed 模式：无操作
        - pool 模式：将账号放回池中
        """
        if self.mode == AllocationMode.POOL:
            async with self._pool_lock:
                self._pool_in_use.pop(profile_id, None)

    def list_accounts(self) -> list[Account]:
        """列出所有账号"""
        return self.accounts.copy()

    def list_profile_ids(self) -> list[str]:
        """列出所有已绑定的 profile ID (fixed 模式)"""
        return list(self._profile_map.keys())

    def available_count(self) -> int:
        """可用账号数量"""
        if self.mode == AllocationMode.FIXED:
            return len(self._profile_map)
        else:
            return len(self.accounts) - len(self._pool_in_use)


account_manager = AccountManager()
