# 提交核对清单（SUBMISSION）

> 本文件为参赛提交自查助手，非赛事必需文件。赛事必需文件见下方核对表。

## 一、赛事必需文件核对（文件名不可改，CONTEST_DECLARATION.md 内容也不可改）

| 序号 | 文件 | 状态 | 说明 |
|---|---|---|---|
| 1 | `README.md` | ✅ 已存在 | 项目介绍、安装、使用示例、目标用户 |
| 2 | `CONTEST_DECLARATION.md` | ✅ 已填官方原文 | **文件名与内容均不可改**，已用官方仓库原文整体覆盖 |
| 3 | `MCP_INTEGRATION.md` | ✅ 已存在 | 实际使用的 MCP Server / Tool / 调用流程 / 业务价值 |
| 4 | `mcp-config.example.json` | ✅ 已存在 | 脱敏 MCP 配置示例，**仅含环境变量占位符** `${MCD_MCP_TOKEN}` |
| 5 | 源代码 | ✅ `SKILL.md` + `scripts/` | 项目主体可运行内容（WorkBuddy Skill 定义 + 编排脚本） |
| 6 | `workbuddy.md` | ✅ 已存在 | 仅参加 WorkBuddy 专项奖励（+3000 积分）时必需，文件名不可改 |

> 规则依据：`activityGuidelines.md` 明确必需文件为 README / CONTEST_DECLARATION / MCP_INTEGRATION / mcp-config.example.json；workbuddy.md 为 WorkBuddy 专项奖励必需。

## 二、GitHub 仓库要求

- 仓库须为 **Public（公开）**。
- **创建时间**：北京时间 2025-12-25 00:00 —— 2026-10-25 23:59 之间（当前时间在此区间内）。
- 同一 GitHub 账号多个参赛项目仅 Star 最高的进榜；多项目同 Star 取最早报名者。
- 账号说明：`beiyucloud` 与 `buyechuanqi` 为同一 GitHub 账号（用户已确认）。

### ⚠️ 自动化阻塞（需你本人授权）

已尝试通过 WorkBuddy 的 **GitHub 连接器代为创建仓库**，返回：
```
403 Resource not accessible by integration
```
即该集成**未被授予写权限（repo scope）**。这属于权限问题而非凭证过期，因此不应按"凭证过期"流程去重新授权。
同时本机**未安装 `gh` CLI**（`gh: command not found`），沙箱网络也限制了 pip 安装第三方库。

**结论**：建仓库 / 推文件 / 发 Issue 的最后授权动作需你本人完成；脚本与命令已全部备好（见第三、四节）。

## 三、一键发布脚本

`scripts/publish.sh` 会依次完成：创建 Public 仓库 → 提交并推送全部文件 → 按官方格式提交参赛 Issue。

```bash
# 1) 安装 GitHub CLI（若未安装）
winget install --id GitHub.cli

# 2) 登录（勾选 repo 权限）
gh auth login

# 3) 一键发布
cd mcd-party-planner
bash scripts/publish.sh
```
脚本可重复执行；仓库已存在时自动跳过创建步骤。

## 四、Issue 报名正文（脚本内已写入，也可手动复制）

```
【参赛申请】
项目名称：麦麦派对官
项目地址：https://github.com/beiyucloud/mcd-party-planner
项目简介：基于麦当劳官方 MCP 的派对主题活动策划助手，端到端串起城市→门店→日期→场次→策划单，用户确认后可下单。
```

> 官方校验要点：
> - 项目地址**不要用 Markdown 链接**，直接贴裸 URL。
> - 字段之间**不要插入多余空行**；`项目简介：` 与简介内容同行。
> - 报名 Issue 需发布在官方活动仓库 `M-China/mcd-developer-innovation-challenge`。

## 五、演示素材

- `assets/real_party_plan.html` —— **实时真实数据**渲染的策划单（上海市 / 麦当劳上海黄浦华旭国际大厦餐厅 / 2026-10-18 / 场次 36946598）。
- `assets/demo.html` —— **自包含动画演示**，自动播放整条链路（spu→城市→门店→日期→场次→策划单）。浏览器打开即可播放；如需 `demo.gif`，用 **Win+G（Xbox Game Bar）** 录屏后覆盖同名文件。
- `assets/party_plan.html` —— 模拟数据版策划单（离线兜底）。

## 六、提交前最终检查

- [x] `CONTEST_DECLARATION.md` 已是官方原文（未手写、未改字）。
- [x] `mcp-config.example.json` 无真实 Token（仅 `${MCD_MCP_TOKEN}`）。
- [x] 全仓库 grep 确认两个测试 Token 均未落盘。
- [x] 实时链路已跑通，`real_data.json` + `real_party_plan.html` 为真实数据。
- [ ] **GitHub 仓库已创建（Public）且创建时间在要求区间内** —— 待你执行
- [ ] **全部文件已推送** —— 跑 `bash scripts/publish.sh` 即可
- [ ] **参赛 Issue 已提交** —— 脚本自动完成
- [ ] （可选）`assets/demo.gif` 已录制并覆盖

## 七、安全提醒

- 两个测试用 MCP Token 曾明文出现在对话中，建议提交/录屏后到 `open.mcd.cn/mcp` **重新生成 / 吊销**。
- 本仓库所有脚本均从环境变量 `MCD_MCP_TOKEN` 读取 Token，不落盘。
