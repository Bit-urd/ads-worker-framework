from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

import yaml


ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
ACCOUNTS_FILE = CONFIG_DIR / "accounts.yaml"


class AllocationMode(Enum):
    FIXED = "fixed"  # 固定绑定
    POOL = "pool"    # 账号池动态分配


class BrowserPlatform(Enum):
    ADSPOWER = "adspower"
    MULTILOGINX = "multiloginx"


@dataclass
class AdsPowerConfig:
    url: str = "http://localhost:50325"
    api_key: str = ""


@dataclass
class MultiloginXConfig:
    launcher_url: str = "https://launcher.mlx.yt:45001"
    token: str = ""
    folder_id: str = "default"  # 默认文件夹 ID


@dataclass
class Config:
    platform: BrowserPlatform = BrowserPlatform.ADSPOWER
    adspower: AdsPowerConfig = field(default_factory=AdsPowerConfig)
    multiloginx: MultiloginXConfig = field(default_factory=MultiloginXConfig)
    concurrency: int = 3
    mode: AllocationMode = AllocationMode.FIXED
    request_timeout: float = 30.0
    accounts_file: Path = ACCOUNTS_FILE

    @classmethod
    def load(cls, file_path: Path | None = None) -> "Config":
        """从 YAML 文件加载配置"""
        file_path = file_path or ACCOUNTS_FILE
        if not file_path.exists():
            return cls()

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # 加载平台选择
        platform_str = data.get("platform", "adspower")
        platform = BrowserPlatform(platform_str)

        # 加载 AdsPower 配置
        ads_cfg = data.get("adspower", {})

        # 加载 MultiloginX 配置
        mlx_cfg = data.get("multiloginx", {})

        mode_str = data.get("mode", "fixed")

        return cls(
            platform=platform,
            adspower=AdsPowerConfig(
                url=ads_cfg.get("url", "http://localhost:50325"),
                api_key=ads_cfg.get("api_key", ""),
            ),
            multiloginx=MultiloginXConfig(
                launcher_url=mlx_cfg.get("launcher_url", "https://launcher.mlx.yt:45001"),
                token=mlx_cfg.get("token", ""),
                folder_id=mlx_cfg.get("folder_id", "default"),
            ),
            concurrency=data.get("concurrency", 3),
            mode=AllocationMode(mode_str),
            accounts_file=file_path,
        )


config = Config.load()
