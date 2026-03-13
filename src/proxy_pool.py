from dataclasses import dataclass


@dataclass
class Proxy:
    """代理配置"""
    host: str
    port: int
    username: str
    password: str

    def to_adspower_config(self) -> dict:
        """转换为 AdsPower user_proxy_config 格式"""
        return {
            "proxy_type": "http",
            "proxy_host": self.host,
            "proxy_port": str(self.port),
            "proxy_user": self.username,
            "proxy_password": self.password,
        }
