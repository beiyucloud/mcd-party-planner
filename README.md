# 麦麦派对官（McDonald's Party Planner · 派对策划 + 积分精算）

> **麦当劳 × WorkBuddy 1024 程序员节 · 程序员创意开发大赛** 参赛作品
> 一个基于麦当劳官方 MCP（mcp.mcd.cn）的 WorkBuddy 技能，包含**两个深耕模块**：
> ① **派对策划单生成器**——把「城市 → 门店 → 日期 → 场次 → 下单」串成端到端闭环，并渲染成可分享的精美策划单；
> ② **积分精算师**——只读你的积分账户，做「积分体检 / 过期预警 / 抽奖评估 / 兑换性价比排行」。

## 为什么做双模块（差异化定位）
公开资料显示 GitHub 上已有 200+ 麦当劳 MCP 仓库，且出现了 `mcctl` 这类**全量集成 35 个工具的综合 CLI**（人格测试 / 省钱 / 下单 / 派对 / 积分 / 网页 Playground / 70 测试 / CI）。本作品不与它比"广度"，而是选两个它**未做深**的角度做透：

| 模块 | 与 mcctl 的差异 | 价值 |
|---|---|---|
| 派对策划单生成器 | mcctl 的派对是「约束求解器」（输出 Top3 场次）；本作品聚焦**把整场派对变成一份可分享的策划单/邀请函**（真实门店+场次+成本+攻略） | 呈现层，互补而非重复 |
| 积分精算师 | mcctl 仅有零散的 `points/redeem/lottery` 子命令；本作品做成**专注的积分看板**（体检+过期预警+抽奖期望+兑换性价比） | 蓝海，零重叠 |

## 特性
- 🎉 **派对端到端策划**：城市 → 门店 → 可约日期 → 场次 → 餐品搭配 → 下单，一气呵成。
- 📋 **可视化策划单**：`party_planner.py` 把方案渲染成 HTML，可一键分享。
- 🪙 **积分精算师**：`points_advisor.py` 只读账户，出积分体检 + 过期预警 + 抽奖评估 + 兑换性价比看板。
- 🛡️ **安全确认机制**：下单 / 支付 / 抽奖等写操作一律等用户明确确认后才执行（积分模块**绝不自动抽奖**）。
- 🧪 **演示兜底**：两个模块均支持 `--offline` 离线样板数据，无需 Token 也能完整演示。

## 目录结构
```
mcd-party-planner/
├── SKILL.md                 # WorkBuddy 技能定义（双模块 + Prompt 模板）
├── README.md                # 本文件
├── CONTEST_DECLARATION.md   # 参赛声明（官方原文，不可改）
├── MCP_INTEGRATION.md       # MCP 工具调用说明
├── mcp-config.example.json  # 脱敏 MCP 配置（仅环境变量占位符）
├── workbuddy.md             # 开发实录（攒 WorkBuddy 专项积分）
├── scripts/
│   ├── party_chain.py       # 派对真实 MCP 链路编排 + 策划单渲染
│   ├── party_planner.py     # 策划单 HTML 生成器
│   ├── demo_data.py         # 派对模拟数据
│   ├── points_advisor.py    # 积分精算师（实时 + 离线）
│   └── mp4_to_gif.py        # 演示视频转 GIF 工具
└── assets/                  # 演示 GIF / 截图 / 看板 HTML
```

## 安装与配置
1. 在 `open.mcd.cn/mcp` 用手机号登录并激活，免费领取 MCP Token。
2. 在 WorkBuddy 连接器填入下方配置，Token 通过环境变量 `MCD_MCP_TOKEN` 注入（**不要写死在文件里**）。
3. 将本仓库作为 WorkBuddy Skill 加载，或直接在工作区对话中调用。

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer ${MCD_MCP_TOKEN}" }
    }
  }
}
```

---

## 模块一：派对策划单生成器

**对话方式**（在 WorkBuddy 中）：
> 用户：帮我看看上海哪个麦当劳能办生日派对，10 月底的。
> 麦麦派对官：先 `mall-points-products` 取派对 spu（如 1779 奇妙生日派对）→ `query-party-city(spuId)` → `query-party-store(code,lat,lon,spuId)`（上海）→ `query-party-store-date` → `query-party-store-session`，返回可约门店 / 日期 / 场次，并生成策划单供确认。

**脚本方式**（本地预览策划单）：
```bash
python scripts/demo_data.py
python scripts/party_planner.py demo_data.json -o assets/party_plan.html
```

### 一条命令出真实策划单
```bash
# 离线（无需 Token，使用真实捕获快照）
python scripts/party_chain.py --offline --out real_data.json --html assets/real_party_plan.html

# 实时（需有效 Token）
MCD_MCP_TOKEN=你的Token python scripts/party_chain.py \
    --party "奇妙生日派对" --city "上海" \
    --out real_data.json --html assets/real_party_plan.html
```
- `--party`：派对主题关键词（匹配 `spuName`），默认「奇妙生日派对」。
- `--city`：目标城市名（模糊匹配），不填则取 API 返回的第一座城市。
- ⚠️ 若报 `401 未授权`，说明 Token 已失效，请到 `open.mcd.cn/mcp` 重新生成后再跑。

---

## 模块二：积分精算师

**对话方式**（在 WorkBuddy 中）：
> 用户：帮我看看我麦当劳积分还剩多少，会不会过期，值不值得抽。
> 麦麦派对官：调用 `query-my-account` 做积分体检 → `query-lottery-info` 评估可抽次数与奖池 → `mall-points-products` 拉可取商品做性价比排行 → 生成积分看板。

**脚本方式**（本地预览看板）：
```bash
# 离线（无需 Token，使用内置样板数据）
python scripts/points_advisor.py --offline --html assets/points_dashboard.html

# 实时（需有效 Token，只读你的账户）
MCD_MCP_TOKEN=你的Token python scripts/points_advisor.py --html assets/points_dashboard.html
```
看板包含：**积分体检 KPI**（可用/累计/已用/冻结）、**过期预警**（本月/下月/上月过期积分）、**抽奖评估**（每次耗分、可抽次数、奖池）、**兑换性价比排行**（每 100 积分≈？元）、**智能建议**。

> 安全：积分模块**仅使用只读工具**（`query-my-account` / `query-lottery-info` / `mall-points-products`），**绝不调用 `draw-lottery` / `mall-create-order` 等写操作**，不消耗你的积分，也不存储账号凭证。

---

## 目标用户
- 想给孩子办生日派对的家长
- 需要团建 / 聚会的组织者
- 想用 AI 一键搞定派对预约 / 厘清积分权益的普通消费者

## 免责声明
- 本作品仅用于 1024 程序员节创意开发大赛，非商业用途。
- 价格、库存、可约场次、积分余额以麦当劳官方 MCP 实时返回为准。
- 遵守《麦当劳 MCP 服务规则》，不暗示官方背书。
