---
name: mcd-party-planner
description: 麦当劳派对/主题活动策划助手。当用户想规划麦当劳生日派对、团建或主题活动，需要查询可参与城市、门店、可预约日期与场次，并生成派对策划方案或完成派对订单下单时使用。基于麦当劳官方 MCP（mcp.mcd.cn）的 query-party-* 工具链实现端到端闭环。
version: 0.1.0
---

# 麦麦派对官（McDonald's Party Planner）

## 适用场景
- 用户想办一场麦当劳生日派对 / 儿童派对 / 团建活动。
- 用户提问如："附近哪有麦当劳能办派对""XX 城市麦当劳派对怎么预约""帮我订一个麦当劳派对"。

## 工具调用流程（严格顺序，已实连验证）
0. `mall-points-products` —— 先查麦麦商城商品，筛选「派对类」拿到 **spuId**（如 1779=麦当劳奇妙生日派对）。这是整条链的主钥匙。
1. `query-party-city(spuId)` —— 查该 spu 可办派对城市（返回 code / latitude / longitude / name）。
2. `query-party-store(code, latitude, longitude, spuId)` —— 查该城市下可办派对门店（取 `storeCode`）。
3. `query-party-store-date(spuId, storeCode)` —— 查该门店可预约日期（取 `date`）。
4. `query-party-store-session(spuId, storeCode, dateStr)` —— 查当天场次（取 `id`、timeStart/timeEnd、partyMin/partyMax、price、leftNum）。
5. （可选）`query-meals` / `query-meal-detail` —— 搭配餐品与套餐。
6. `party-order-create(partyType, spuId, storeCode, dateStr, id, ...)` —— 用户确认后下单（partyType：1-包场 / 2-拼团），返回订单与支付链接。

## 输出物
- 向用户复述选定的「城市 / 门店 / 日期 / 场次 / 人数」，并用 `scripts/party_planner.py` 生成一份可视化策划单（HTML）供确认。
- 用户确认后调用 `party-order-create` 下单，返回支付链接。

## 注意事项
- 所有下单 / 支付动作必须等用户**明确确认**后再执行；支付由用户本人完成。
- 若 `query-party-city` 返回空，说明当前无开放的主题活动，应如实告知用户，**不得编造数据**。
- 演示 / 测试可依赖 `scripts/demo_data.py` 生成的模拟数据，但正式回答用户须以 MCP 实时返回为准。
- 遵守麦当劳 MCP 服务规则，非商业用途，Token 仅本人使用、不泄露。

---

## 可直接粘贴的自然语言 Prompt 模板

> 用法：在 WorkBuddy 对话框中粘贴以下任一整段文字即可触发派对官流程。无需记忆工具名，模型会按「工具调用流程」自动编排 `query-party-*` 链路。方括号 `[ ]` 处请按实际情况替换。

### 模板 1 · 探索可办派对的城市（入门）
```
请帮我查一下麦当劳现在能办哪些主题的派对活动，分别有哪些城市可以办？
用 mcd-party-planner 技能，先查麦麦商城的派对类商品，再列出每个派对活动对应的可办城市（至少给我前 5 个城市的名字）。
```

### 模板 2 · 指定城市找门店 + 日期（最常用）
```
我想在[城市名，如：上海]办一场[派对类型，如：奇妙生日派对]的麦当劳派对。
请用 mcd-party-planner 帮我：
1. 找到该派对的 spuId；
2. 列出[城市名]下可办派对的麦当劳门店；
3. 挑一家离市中心近的，列出它最近可预约的 5 个日期和当天场次（时间、成团人数、价格、余位）。
```

### 模板 3 · 生成可视化策划单（展示用）
```
基于刚才查到的[门店名]、[日期]、[场次]信息，用 mcd-party-planner 的 scripts/party_planner.py 给我生成一份派对策划单 HTML，
包含：派对主题、门店、日期、场次时间、成团人数、单价、以及我准备邀请[人数]人的预算合计。生成完告诉我文件在哪。
```

### 模板 4 · 完整闭环到下单（涉及真实支付，需本人确认）
```
我想在[城市名]的[门店名]办[派对类型]派对，日期定[YYYY-MM-DD]，场次选[场次时间]，打算邀请[人数]人。
请用 mcd-party-planner 走完整流程：查 spuId → 校验门店/日期/场次 → 生成策划单让我确认。
⚠️ 确认无误后只返回 party-order-create 需要的参数和支付链接，不要自动下单，等我最后点确认。
```

### 模板 5 · 演示 / 录屏（无需真实 Token 也可用）
```
请载入 mcd-party-planner 技能，用 scripts/demo_data.py 生成一份模拟派对数据，
再调用 scripts/party_planner.py 渲染成 party_plan.html 策划单。我要用它录一段 demo 视频，不需要真实下单。
```

### 进阶 · 一句话触发（已熟悉流程的用户）
```
@mcd-party-planner 上海 奇妙生日派对 10月底 帮我出策划单
```

---

## 触发检查清单（排错用）
- [ ] MCP 已连接：WorkBuddy 设置里 mcp.mcd.cn 的 Bearer Token 已填（环境变量 `MCD_MCP_TOKEN`）。
- [ ] 工具可见：`/mcp` 或技能面板能看到 `query-party-*` 系列工具，否则重启 WorkBuddy 重连。
- [ ] 报错 400「缺少参数」：检查是否先取了 `spuId`，且 store 调用带了 `code/latitude/longitude/spuId`。
- [ ] 城市/门店返回空：该 spu 当前可能未开放此类活动，换模板 1 看全局开放情况。
