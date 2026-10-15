#!/usr/bin/env bash
# 麦麦派对官 · 一键发布到 GitHub 并提交参赛 Issue
#
# 前置条件：
#   1. 已安装 GitHub CLI：winget install --id GitHub.cli
#   2. 已登录（需勾选 repo 权限）：gh auth login
#
# 用法：
#   bash scripts/publish.sh
#
# 说明：脚本全程可重复执行；仓库已存在时会跳过创建步骤。

set -euo pipefail

OWNER="beiyucloud"
REPO="mcd-party-planner"
DESC="麦麦派对官 | 麦当劳 x WorkBuddy 1024 程序员节创意开发大赛参赛作品：基于麦当劳官方 MCP 的派对主题活动策划 Skill，端到端串起城市→门店→日期→场次→策划单→下单。"

OFFICIAL_OWNER="M-China-Official"
OFFICIAL_REPO="mcd-developer-innovation-challenge"

# 切到项目根目录（scripts/ 的上一级）
cd "$(dirname "$0")/.."

echo "==> 1/4 检查 GitHub CLI"
if ! command -v gh >/dev/null 2>&1; then
  echo "未检测到 gh，请先安装：winget install --id GitHub.cli"
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "gh 未登录，请先执行：gh auth login（勾选 repo 权限）"
  exit 1
fi
echo "    gh 已就绪（账号：$OWNER）"

echo "==> 2/4 创建 Public 仓库（如已存在则跳过）"
if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  echo "    仓库 $OWNER/$REPO 已存在，跳过"
else
  gh repo create "$REPO" --public --description "$DESC" --confirm
  echo "    已创建 $OWNER/$REPO"
fi

echo "==> 3/4 提交并推送全部文件"
if [ ! -d .git ]; then
  git init -b main
fi
# 若本机未配置 git 身份，临时写入仓库级配置（不污染全局）
if [ -z "$(git config user.name 2>/dev/null || true)" ]; then
  git config user.name "$OWNER"
fi
if [ -z "$(git config user.email 2>/dev/null || true)" ]; then
  git config user.email "$OWNER@users.noreply.github.com"
fi
git add -A
if git diff --cached --quiet; then
  echo "    无变更可提交"
else
  git commit -m "feat: 麦麦派对官 — 基于麦当劳官方 MCP 的派对策划 Skill（含真实链路编排与策划单渲染）"
fi
git branch -M main
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$OWNER/$REPO.git"
git push -u origin main
echo "    推送完成"

echo "==> 4/4 提交参赛 Issue"
REPO_URL="https://github.com/$OWNER/$REPO"
# ⚠️ 官方校验要求：
#   - 项目地址不使用 Markdown 链接格式（直接贴裸 URL）
#   - 字段之间不要插入多余空行；"项目简介：" 与简介内容同行
ISSUE_BODY="$(printf '【参赛申请】\n项目名称：麦麦派对官\n项目地址：%s\n项目简介：基于麦当劳官方 MCP 的派对主题活动策划助手，端到端串起城市→门店→日期→场次→策划单，用户确认后可下单。' "$REPO_URL")"

gh issue create \
  --repo "$OFFICIAL_OWNER/$OFFICIAL_REPO" \
  --title "麦麦派对官参赛申请" \
  --body "$ISSUE_BODY"

echo "✅ 全部完成"
