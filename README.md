# AdsPower Worker Framework

AdsPower 多环境自动化框架，支持 Playwright 业务逻辑编写。

## 目录结构

```
ads-worker-framework/
├── config/                  # 配置目录
│   ├── accounts.yaml        # 账号配置
│   └── accounts.example.yaml
├── src/                     # 核心框架
├── tasks/                   # 用户任务
│   └── examples.py          # 示例任务
├── logs/                    # 日志目录
├── main.py                  # 生产环境入口
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
uv sync
playwright install chromium
```

### 2. 配置账号

复制配置模板：
```bash
cp config/accounts.example.yaml config/accounts.yaml
```

编辑 `config/accounts.yaml`：

```yaml
# AdsPower 配置
adspower:
  url: "http://localhost:50325"
  api_key: ""

concurrency: 3

# 分配模式: fixed (固定绑定) 或 pool (账号池)
mode: fixed

accounts:
  - name: "account_001"
    profile_id: "xxx"  # AdsPower 环境 ID
    proxy:
      host: "geo.iproyal.com"
      port: 12321
      username: "user"
      password: "pass"
    web3:
      address: "0x..."
      private_key: "..."
```

### 3. 编写任务

在 `tasks/` 目录下创建任务：

```python
from playwright.async_api import Page
from src import register, BaseWorker

@register("my_task")
class MyTask(BaseWorker):
    async def run(self, page: Page):
        # 访问账号信息
        wallet = self.account.web3.get("private_key")
        proxy = self.account.proxy

        # 业务逻辑
        await page.goto("https://example.com")

        return {"done": True}
```

### 4. 运行方式

#### 开发模式（独立浏览器调试）

直接启动 Playwright 浏览器测试任务逻辑，无需 AdsPower：

```bash
# 编辑 tasks/examples.py 的 dev_run() 函数
# 选择要测试的任务，然后运行：
uv run python tasks/examples.py
```

#### 生产模式（AdsPower 环境）

```bash
# 列出所有任务
uv run python main.py --list

# 列出所有账号
uv run python main.py --accounts

# 运行单个任务
uv run python main.py --task check_ip

# 运行多个任务（共用 profile 和账号）
uv run python main.py --task check_ip --task web3_example

# 指定并发数
uv run python main.py --task check_ip -c 5
```

## 两种分配模式

### Fixed 模式（固定绑定）

- 每个账号指定 `profile_id`
- 1:1 长期绑定
- 适合养号场景

```yaml
mode: fixed
accounts:
  - name: "account_001"
    profile_id: "xxx"
    proxy: ...
```

### Pool 模式（账号池）

- `profile_id` 可选
- 动态分配账号给 profile
- 用完释放回池子
- 适合批量任务（如 10 profile 轮流用 30 账号）

```yaml
mode: pool
accounts:
  - name: "pool_001"
    proxy: ...
```

