# 麦麦派对官（McDonald's Party Planner）

> **麦当劳 × WorkBuddy 1024 程序员节 · 程序员创意开发大赛** 参赛作品
> 基于麦当劳官方 MCP（mcp.mcd.cn）的派对主题活动工具链，把「城市 → 门店 → 日期 → 场次 → 下单」串成一条端到端闭环。

## 为什么做这个选题
公开资料显示，GitHub 上已有 200+ 麦当劳 MCP 仓库，红海集中在**省钱 / 优惠券、健身餐卡路里、点餐助手、生日惊喜**等方向。而 `query-party-*`（派对 / 主题活动）这组工具**几乎无人做**——它是一条比点餐更长的决策闭环，且天然适合做"策划单"可视化，差异化明显、演示出彩。

## 特性
- 🎉 **端到端派对策划**：城市 → 门店 → 可约日期 → 场次 → 餐品搭配 → 下单，一气呵成。
- 📋 **可视化策划单**：用 `scripts/party_planner.py` 把方案渲染成 HTML，用户一眼看清。
- 🛡️ **安全确认机制**：涉及下单 / 支付的动作一律等用户明确确认后才执行。
- 🧪 **演示兜底**：内置 `demo_data.py` 模拟数据，即使官方暂未开放活动，demo 也能跑通。

## 目录结构
```
mcd-party-planner/
├── SKILL.md                 # WorkBuddy 技能定义
├── README.md                # 本文件
├── CONTEST_DECLARATION.md   # 参赛声明（须填官方原文）
├── MCP_INTEGRATION.md       # MCP 工具调用说明
├── mcp-config.example.json  # 脱敏 MCP 配置
├── workbuddy.md             # 开发实录（攒 WorkBuddy 专项积分）
├── scripts/
│   ├── party_chain.py       # 真实 MCP 链路编排（city→store→date→session）+ 渲染
│   ├── party_planner.py     # 策划单 HTML 生成器
│   └── demo_data.py         # 演示用模拟数据
└── assets/                  # 演示 GIF / 截图
```

## 安装与配置
1. 在 `open.mcd.cn/mcp` 用手机号登录并激活，免费领取 MCP Token。
2. 在 WorkBuddy 连接器填入 `mcp-config.example.json` 的内容，Token 通过环境变量 `MCD_MCP_TOKEN` 注入（**不要写死在文件里**）。
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

## 使用示例
**对话方式**（在 WorkBuddy 中）：
> 用户：帮我看看上海哪个麦当劳能办生日派对，10 月底的。
> 麦麦派对官：先 `mall-points-products` 取派对 spu（如 1779 奇妙生日派对）→ `query-party-city(spuId)` → `query-party-store(code,lat,lon,spuId)`（上海）→ `query-party-store-date` → `query-party-store-session`，返回可约门店 / 日期 / 场次，并生成策划单供确认。

**脚本方式**（本地预览策划单）：
```bash
# 模拟数据（无需 Token）
python scripts/demo_data.py
python scripts/party_planner.py demo_data.json -o assets/party_plan.html
```

## 快速开始：一条命令出真实策划单

脚本 `scripts/party_chain.py` 会把整条麦当劳 MCP 链路真实跑通，并直接渲染策划单 HTML。

### 离线模式（无需 Token，使用 2026-10-15 真实捕获快照）
```bash
python scripts/party_chain.py --offline \
    --out real_data.json --html assets/real_party_plan.html
```

### 真实模式（需有效 Token，实时抓取）
```bash
MCD_MCP_TOKEN=你的Token \
python scripts/party_chain.py \
    --party "奇妙生日派对" --city "上海" \
    --out real_data.json --html assets/real_party_plan.html
```
- `--party`：派对主题关键词（匹配 `spuName`），默认「奇妙生日派对」。
- `--city`：目标城市名（模糊匹配），不填则取 API 返回的第一座城市。
- 输出：中间数据 `real_data.json` + 渲染好的 `assets/real_party_plan.html`。
- ⚠️ 若报 `401 未授权`，说明 Token 已失效，请到 `open.mcd.cn/mcp` 重新生成后再跑。

> 在 WorkBuddy 对话框里，也可以用 [SKILL.md 末尾的现成 Prompt 模板](SKILL.md) 直接触发，无需记忆工具名。

## 目标用户
- 想给孩子办生日派对的家长
- 需要团建 / 聚会的组织者
- 想用 AI 一键搞定派对预约的普通消费者

## 免责声明
- 本作品仅用于 1024 程序员节创意开发大赛，非商业用途。
- 价格、库存、可约场次以麦当劳官方 MCP 实时返回为准。
- 遵守《麦当劳 MCP 服务规则》，不暗示官方背书。
