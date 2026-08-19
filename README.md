# AI Ledger — 个人现金流终端

> 核心公式：**工资 = 日常开销 + 贷款 + 结余**。这个工具帮你预测月结余与年结余，并在"想买个大件"时沙盘试算现金流是否扛得住。

单用户、低门槛、AI 优先：日常记账通过 Agent 调 MCP 完成，Web UI 负责随时查看（桌面 + 移动浏览器）。

## 架构

```
Agent(CodeBuddy 等) --Streamable HTTP /mcp--> FastAPI --+--> engine(纯函数计算引擎)
Web UI(桌面/移动)  --REST /api/v1---------->          +--> service(业务规则)
                                                      +--> SQLite(金额整数分)
```

- 后端：FastAPI + SQLAlchemy + SQLite，token 鉴权（REST 与 MCP 统一 Bearer）
- MCP：fastmcp Streamable HTTP，挂在 `/mcp`
- 前端：Vue3 + Naive UI + Tailwind + ECharts，绿黑极客风，移动端优先
- 计算引擎：`server/engine/` 纯函数（等额本息/本金摊还、结余预测、沙盘试算），pytest 全覆盖

## 本地开发

```bash
# 后端（Python 3.12+）
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.main:app --reload --port 18731

# 前端（另开终端）
cd web && npm install && npm run dev   # vite dev 代理 /api 与 /mcp 到 18731

# 或者构建后由后端直接托管（单端口）
cd web && npm run build && cd .. && uvicorn server.main:app --port 18731
# 打开 http://127.0.0.1:18731/ ，token 默认 dev-token（API_TOKEN 环境变量可改）

# 测试
pytest tests/ -q
```

## 部署到 Lighthouse（Docker）

```bash
cp .env.example .env   # 修改 API_TOKEN 为强随机串
docker compose up -d --build
# 防火墙放行 8000；Web UI 与 /mcp 均在 8000 端口
# SQLite 落在 named volume ledger-data，重启/升级不丢数据
```

## Agent 端 MCP 配置

Streamable HTTP 类型：

```json
{
  "mcpServers": {
    "ai-ledger": {
      "type": "streamable-http",
      "url": "http://<host>:8000/mcp/",
      "headers": { "Authorization": "Bearer <API_TOKEN>" }
    }
  }
}
```

### 可用工具

| 工具 | 说明 | 示例口语 |
|---|---|---|
| `add_expense` | 记支出（金额/分类/备注） | "午饭花了 35" |
| `add_income` | 记收入（奖金/意外收入） | "年终奖到账 5w" |
| `add_loan` | 建贷款/分期（总额+期数+利率，自动摊还） | "车贷 12w 分 24 期年利率 4.5" |
| `add_recurring` | 每月固定收支（工资/房租） | "我月薪 2.5w 每月 10 号发" |
| `get_cashflow_forecast` | 未来 N 月结余预测 + 年结余 | "我今年能剩多少钱" |
| `simulate_purchase` | 沙盘试算分期购买（不落库） | "想分 12 期买 2w 的相机，扛得住吗" |
| `list_recent` | 最近流水 | "我最近记了什么账" |
| `get_dashboard` | 本月概览 | "这个月收支情况" |

## 数据口径

- 金额全程整数分存储，利率基点存储，仅展示层转元
- 月供按"当月发生即计入当月"，不按精确日切分
- 结余 = 收入(recurring + 流水) − 固定支出 − 贷款月供 − 日常开销流水
