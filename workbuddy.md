# 开发实录（workbuddy.md）

> 本文件记录使用 WorkBuddy 开发「麦麦派对官」的全过程，用于领取 WorkBuddy 专项积分（+3000）。

## 开发环境
- 平台：WorkBuddy（Agent 模式）
- 语言：Python 3.13（仅标准库，无第三方依赖）
- MCP：`mcd-mcp`（https://mcp.mcd.cn，Streamable HTTP）

## 开发时间线
1. **选题调研**：检索官方仓库 `M-China/mcd-mcp-server` v1.0.9，核对约 35 个真实工具；扫描公开参赛作品，确认 `query-party-*` 派对链为蓝海方向。
2. **方案草案**：产出 `mcd-workbuddy-contest-plan.md`，列出主方案（积分精算师）与备选（派对官 / 年度账单）。
3. **确定选题**：用户选定备选 A —— 麦麦派对官。
4. **脚手架搭建**（WorkBuddy 直接生成）：
   - `SKILL.md`：技能定义 + 工具调用顺序。
   - 五个必需文件：`README.md` / `CONTEST_DECLARATION.md`（待填官方原文）/ `MCP_INTEGRATION.md` / `mcp-config.example.json` / `workbuddy.md`。
   - `scripts/party_planner.py`：派对策划单 HTML 生成器（纯标准库）。
   - `scripts/demo_data.py`：演示用模拟数据，解决派对工具可能无实时数据的演示风险。
5. **待办**：用户领取 MCP Token 后实连测试；录制 `assets/demo.gif`；复制官方参赛声明原文；提交 GitHub + Issue 报名。

## 关键决策
- **差异化**：避开省钱 / 卡路里红海，选派对主题活动长链路。
- **演示兜底**：内置模拟数据，保证 demo 始终可跑。
- **安全**：下单 / 支付动作全部用户确认后执行。

## 验证
```bash
python scripts/demo_data.py
python scripts/party_planner.py demo_data.json -o assets/party_plan.html
# 预期：生成 assets/party_plan.html 策划单
```

## 实连验证（2026-10-15）
用户提供 MCP Token（仅通过环境变量传入脚本，未写入任何项目文件）。实测结论：
- `initialize` 成功返回 `mcd-mcp v1.0.0`，`tools/list` 共 35 个工具。
- `mall-points-products` 返回 **18 个派对类商品**（spuId=1779 奇妙生日派对等）。
- 完整链路只读跑通：`query-party-city(1779)`→281 城市；`query-party-store`→门店；`query-party-store-date`→9 日期；`query-party-store-session`→2 场次（id=36888219，12:00–13:30，5–12 人，¥50，余位 12）。
- **修正**：官方 README 工具名笔误（`query-partystore-*` 应为 `query-party-store-*`），且流程缺 spuId 入口（需先 `mall-points-products` 取派对 spuId）。已同步修正 SKILL.md / MCP_INTEGRATION.md / README.md。
- 价格单位：spu 级 price 为元，场次级 price 为分，展示需换算。

## 迭代追加（2026-10-15 晚）
- 在 `SKILL.md` 末尾新增「可直接粘贴的自然语言 Prompt 模板」段：覆盖 5 个场景（探索城市 / 指定城市找门店 / 生成策划单 / 闭环下单 / 演示录屏）+ 一句触发 + 排错检查清单，让用户无需记忆工具名即可在 WorkBuddy 对话框直接粘贴使用。
- 新增 `scripts/party_chain.py`：真实跑通麦当劳 MCP 端到端只读链路（mall-points-products 取 spu → query-party-city → query-party-store → query-party-store-date → query-party-store-session），自动映射为 party_planner.py 入参并渲染真实策划单 HTML。支持 `--offline`（内置 2026-10-15 真实捕获快照，无需 Token）与实时两种模式；401 时给出友好提示。README 已加「快速开始：一条命令出真实策划单」章节。
- **Token 失效**：23:53 复测同一 Token 对 `initialize` 已返回 401（23:3x 时可用），判断该 Token 已被吊销/过期（应归功于此前"测试后轮换"建议，或自动失效）。故无法实时重抓；改用 `--offline` 快照渲染出 `assets/real_party_plan.html`（2.6KB，已标注非实时）。待用户提供新 Token 即可一条命令出实时策划单。
- **实时跑通（2026-10-15 23:55）**：用户提供新 Token 后，`party_chain.py` 实时模式一次成功（只读）。真实结果：spuId=1779 麦当劳奇妙生日派对 → 城市=上海市(code=310100) → 门店=麦当劳上海黄浦华旭国际大厦餐厅(storeCode=1450713) → 日期=2026-10-18 → 场次 id=36946598（12:00-13:30，5-12 人成团，¥50，余位 12）。已写出 `real_data.json` 并渲染 `assets/real_party_plan.html`（**实时真实数据**，非快照）。证明派对官端到端可用。

## 对齐官方规范（2026-10-15 23:59，用户提供官方仓库 zip）
- 用户提供官方源 `mcd-developer-innovation-challenge-main.zip`，解压至 `mcd-official-source/` 核对。
- **CONTEST_DECLARATION.md 已用官方原文整体覆盖**（文件名与内容均不可改，无签名/署名行，须原样保留）；此前为占位说明已废弃。
- 确认 `activityGuidelines.md` 必需文件：README / CONTEST_DECLARATION / MCP_INTEGRATION / **mcp-config.example.json（仅环境变量占位符）**；workbuddy.md 为 WorkBuddy 专项奖励必需。本仓库 4 个必需文件 + workbuddy.md 均已齐备；mcp-config.example.json 使用 `${MCD_MCP_TOKEN}` 占位，合规。
- grep 全仓库确认两个测试 Token 均未落盘（符合声明"不含真实凭证"要求）。
- 新增 `SUBMISSION.md`：必需文件核对表 + Issue 报名草稿（含官方强调的"链接不用 Markdown、标题/正文/简介间不留空行"等格式坑）+ GitHub 仓库创建时间(2025-12-25~2026-10-25)与 Public 要求 + 安全提醒。
- **账号澄清**：用户确认 `beiyucloud` 与 `buyechuanqi` 是同一 GitHub 账号，仓库建在 `beiyucloud` 下无歧义。
- **自动化阻塞 1（GitHub 写权限）**：尝试用 WorkBuddy GitHub 连接器代为创建仓库，返回 `403 Resource not accessible by integration`——集成未被授予 repo 写权限，属权限问题而非凭证过期，故不走"凭证过期"的重新授权流程。本机未装 `gh` CLI。因此建仓库/推文件/发 Issue 的最后授权动作需用户本人完成。
- **自动化阻塞 2（屏幕录像）**：无法做屏幕录像生成 demo.gif；沙箱网络受限，pip 走清华镜像找不到 pillow，无法程序化生成 GIF。
- **替代交付**：新增 `assets/demo.html` —— 自包含动画演示（自动播放 spu→城市→门店→日期→场次→策划单整条真实链路），浏览器直接打开即可播放；用户可用 Win+G 录屏覆盖为 demo.gif。
- **一键脚本**：新增 `scripts/publish.sh`（gh 驱动）：创建 Public 仓库 → 提交推送全部文件 → 按官方格式提交 Issue；可重复执行，仓库已存在则跳过创建。
- 项目共 20 个文件，必需文件全部齐备（README / CONTEST_DECLARATION / MCP_INTEGRATION / mcp-config.example.json / 源代码 / workbuddy.md）。

## 重试与网络诊断（2026-10-16 00:2x）
- 再次尝试 MCP `create_repository` → 仍 `403 Resource not accessible by integration`，确认连接器为只读作用域。
- 改走本地 git：首次 `git push` 报 `CRYPT_E_NO_REVOCATION_CHECK`（schannel 吊销检查失败）。
- 定位到环境存在 MITM 代理 `http://127.0.0.1:15006`，且系统 CA 根证书包在
  `C:/Users/Administrator/.workbuddy/system-ca-bundle.pem`（由 `NODE_EXTRA_CA_CERTS` 暴露）。
- 关闭吊销检查（`http.schannelCheckRevoke=false`）无效；改用 **openssl 后端 + 系统 CA 包**后
  `git ls-remote` 成功连通 GitHub（远端正常返回 "Repository not found"）。
- 已把该修复写入仓库 git 配置，并同步进 `scripts/publish.sh`。
- 用 MCP 检索确认 `beiyucloud/mcd-party-planner` 当前不存在（`total_count:0`），故仍需用户本人建仓后推送。
- 本地仓库已就绪：2 个提交（`666fabf` 主体 + `3c66ec5` 文档修复），工作区干净。

## 安全提示
- 用户曾在对话中明文提供 MCP Token，已建议到 open.mcd.cn/mcp 控制台重新生成 / 吊销。所有脚本仅从环境变量 `MCD_MCP_TOKEN` 读取，不写入任何项目文件。
