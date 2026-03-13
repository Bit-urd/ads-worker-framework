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


@dataclass
class AdsPowerConfig:
    url: str = "http://localhost:50325"
    api_key: str = ""


@dataclass
class Config:
    adspower: AdsPowerConfig = field(default_factory=AdsPowerConfig)
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

        ads_cfg = data.get("adspower", {})
        mode_str = data.get("mode", "fixed")

        return cls(
            adspower=AdsPowerConfig(
                url=ads_cfg.get("url", "http://localhost:50325"),
                api_key=ads_cfg.get("api_key", ""),
            ),
            concurrency=data.get("concurrency", 3),
            mode=AllocationMode(mode_str),
            accounts_file=file_path,
        )


config = Config.load()
