"""
测试 MultiloginX 集成

运行前需要：
1. 启动 MultiloginX Launcher
2. 配置正确的 API token
3. 有可用的浏览器配置文件
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import config, multiloginx, get_browser_client, BrowserPlatform


def test_multiloginx_client():
    """测试 MultiloginX 客户端基本功能"""
    print(f"当前平台: {config.platform}")
    print(f"Launcher URL: {config.multiloginx.launcher_url}")

    # 检查服务状态
    status = multiloginx.check_status()
    print(f"MultiloginX 服务状态: {'运行中' if status else '未运行'}")

    if status:
        # 测试启动浏览器（需要有效的 profile_id）
        # profile_id = "your-profile-id-here"
        # browser_data = multiloginx.start_browser(
        #     profile_id=profile_id,
        #     folder_id=config.multiloginx.folder_id,
        #     headless=False,
        #     automation_type="playwright"
        # )
        # print(f"浏览器启动成功: {browser_data}")

        # # 停止浏览器
        # multiloginx.stop_browser(profile_id)
        # print("浏览器已停止")
        pass


def test_platform_switching():
    """测试平台切换"""
    print(f"\n当前配置的平台: {config.platform}")

    # 获取浏览器客户端
    client = get_browser_client()
    print(f"获取到的客户端类型: {type(client).__name__}")

    # 检查状态
    status = client.check_status()
    print(f"平台服务状态: {'运行中' if status else '未运行'}")


if __name__ == "__main__":
    print("=" * 50)
    print("MultiloginX 集成测试")
    print("=" * 50)

    test_multiloginx_client()
    test_platform_switching()

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
