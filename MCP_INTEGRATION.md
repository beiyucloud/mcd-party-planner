# MCP 集成说明（MCP_INTEGRATION）

## 使用的 MCP Server
- **名称**：`mcd-mcp`
- **地址**：`https://mcp.mcd.cn`
- **协议**：Streamable HTTP
- **鉴权**：`Authorization: Bearer ${MCD_MCP_TOKEN}`（Token 在 open.mcd.cn/mcp 免费领取）

## 实际调用的工具（来自 M-China/mcd-mcp-server v1.0.9）

### 核心：派对主题活动工具链
| 工具 | 必填参数 | 用途 | 调用顺序 |
|---|---|---|---|
| `mall-points-products` | 无 | 查麦麦商城商品，筛选「派对类」拿 spuId（链入口） | 0 |
| `query-party-city` | `spuId` | 查该 spu 可办派对城市（code/lat/lon/name） | 1 |
| `query-party-store` | `code`,`latitude`,`longitude`,`spuId` | 查该城市可办派对门店（取 storeCode） | 2 |
| `query-party-store-date` | `spuId`,`storeCode` | 查门店可预约日期（取 date） | 3 |
| `query-party-store-session` | `spuId`,`storeCode`,`dateStr` | 查当天场次（id/time/人数/price/余位） | 4 |
| `party-order-create` | `partyType`(+spuId/storeCode/dateStr/id 等) | 用户确认后创建派对订单，返回支付链接 | 6 |

> ⚠️ 工具名以实连 `tools/list` 为准：`query-party-store-date` / `query-party-store-session`（带连字符）。官方 README 笔误为 `query-partystore-*`，此处已修正。

### 辅助：餐品搭配
| 工具 | 用途 |
|---|---|
| `query-meals` | 查询门店可售餐品，用于派对餐品搭配 |
| `query-meal-detail` | 查询套餐组成 / 可替换项 |

## 调用流程（业务价值，已实连验证）
```
用户意图（办派对）
   │
   ├─ mall-points-products ─► 找派对 spu（如 1779 奇妙生日派对）★ 链入口
   ├─ query-party-city(spuId) ─► 可办城市（实测 281 城，取 code/lat/lon）
   ├─ query-party-store(code,lat,lon,spuId) ─► 门店（取 storeCode）
   ├─ query-party-store-date(spuId,storeCode) ─► 可约日期
   ├─ query-party-store-session(spuId,storeCode,dateStr) ─► 当天场次
   ├─ query-meals（可选） ─► 餐品搭配
   ├─ party_planner.py ─► 生成可视化策划单（HTML）供确认
   └─ party-order-create（用户确认后） ─► 订单 + 支付链接
```

## 真实验证结果（2026-10-15 实连只读测试）
- Token 有效：`initialize` 返回 `mcd-mcp v1.0.0`，`tools/list` 共 **35 个工具**。
- `mall-points-products` 返回 **18 个派对类商品**；选用 `spuId=1779`（麦当劳奇妙生日派对，¥50，status=2 上架）。
- 完整链路跑通：`city(281 城)` → `store(2 门店)` → `date(9 日期)` → `session(2 场次)`。
- 场次示例：`id=36888219`，`12:00–13:30`，成团 `5–12 人`，`price=5000`(**分**=¥50)，`leftNum=12`。
- 价格单位注意：spu 级 `price` 为**元**，场次级 `price` 为**分**，展示时需换算。
**业务价值**：将原本需要在 App 内多次点击、跨页面比对的派对预约流程，压缩成一句自然语言请求；并用可视化策划单降低用户的决策成本。这是点餐 / 省钱类 Skill 未覆盖的"长链路 + 强场景"空白。

## 错误处理
- `query-party-city` 返回空 → 如实告知用户当前无开放活动，**不编造**。
- 429 限流（>600 次/分钟）→ 脚本对 MCP 调用加节流。
- Token 失效（401）→ 提示用户重新在 open.mcd.cn/mcp 激活。
