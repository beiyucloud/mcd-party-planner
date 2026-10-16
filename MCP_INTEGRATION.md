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

### 积分精算模块工具链（只读）
| 工具 | 必填参数 | 用途 | 调用顺序 |
|---|---|---|---|
| `query-my-account` | 无 | 查积分账户：可用/累计/已用/冻结 + 本月(`currentMouthExpirePoint`)/下月(`nextMouthExpirePoint`)/上月(`lastMouthExpirePoint`)过期积分 | 1 |
| `query-lottery-info` | 无 | 查抽奖：每次耗分 `drawPoint`、可抽判定 `drawDecision`、奖池 `prizes` | 2 |
| `mall-points-products` | `catRuleIds`(可选) | 查可兑换商品：取 `point`(积分价) 与 `price`(面值) 算性价比 | 3 |

> ⚠️ **安全红线**：积分模块**仅使用上述只读工具**。**绝不调用 `draw-lottery`（消耗积分抽奖）或 `mall-create-order`（下单）等写操作**；任何消耗积分的动作必须等用户明确确认。真实账号数据仅在内存渲染，不写入仓库。

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

## 积分模块验证（2026-10-16 实连只读测试）
- `query-my-account` 返回字段已核对：`availablePoint` / `accumulativePoint` / `usedPoint` / `frozenPoint` / `currentMouthExpirePoint` / `nextMouthExpirePoint` / `lastMouthExpirePoint`（注意官方字段拼写是 `Mouth` 非 `Month`）。
- `query-lottery-info` 实测：`drawPoint=24`，`drawDecision.resourceEligible` 字段可直接判断是否可抽；奖池为若干优惠券。
- `mall-points-products` 实测：返回商品含 `spuName` / `point`(积分价) / `price`(面值) / `catName`，可据此做性价比排行。
- 积分模块脚本 `points_advisor.py` 实时 + 离线双模式均实跑通过；**未调用任何写操作**。
- 业务价值：把"积分会不会过期、抽还是换、换哪个最值"这类需要跨多个页面、手动比对的决策，压缩成一次查询 + 一张看板，且零风险（只读）。
