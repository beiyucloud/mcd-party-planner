#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦积分精算师 (McPoints Advisor)
=================================
基于麦当劳官方 MCP 的只读能力，做三件事：
  1. 积分体检   -> query-my-account（可用/累计/冻结/已用 + 本月/下月/上月过期积分）
  2. 过期预警   -> 依据 account 的过期字段，提示即将作废的积分
  3. 抽奖评估   -> query-lottery-info（每次耗分、可抽次数、奖池）
  4. 兑换排行   -> mall-points-products（筛选积分价>0 的商品，按 价值密度 排序）

安全原则：
  - 仅使用只读工具；绝不调用 draw-lottery / mall-create-order 等写操作。
  - Token 仅通过环境变量 MCD_MCP_TOKEN 传入，不写入任何文件。
  - 真实账号数据不持久化到仓库（仅内存渲染）。

用法：
  离线演示（无需 Token）：
    python points_advisor.py --offline --html assets/points_dashboard.html
  实时（需 Token）：
    MCD_MCP_TOKEN=xxx python points_advisor.py --html assets/points_dashboard.html
"""
import os
import sys
import json
import re
import argparse
import urllib.request
from pathlib import Path

BASE = "https://mcp.mcd.cn"
TOKEN = os.environ.get("MCD_MCP_TOKEN")
_session = None


# ---------------------------------------------------------------------------
# MCP 传输层（Streamable HTTP）
# ---------------------------------------------------------------------------
def post(payload):
    global _session
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    if _session:
        req.add_header("Mcp-Session-Id", _session)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", "replace")
            _session = (resp.headers.get("Mcp-Session-Id")
                        or resp.headers.get("mcp-session-id") or _session)
            return body
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("401 未授权：Token 无效或已过期，请到 open.mcd.cn/mcp 重新生成后重试。")
        raise


def call(name, args):
    raw = post({"jsonrpc": "2.0", "id": 99, "method": "tools/call",
                "params": {"name": name, "arguments": args}})
    res = json.loads(raw) if raw.strip().startswith("{") else {}
    r = res.get("result", {})
    sc = r.get("structuredContent")
    if sc is not None:
        return sc
    txt = (r.get("content") or [{}])[0].get("text", "")
    i = txt.find("## Original Response")
    if i >= 0:
        m = re.search(r"\{.*\}", txt[i:], re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return {"_raw": m.group(0)[:400]}
    return {"_raw": txt[:400]}


def init():
    global _session
    post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                     "clientInfo": {"name": "mcpoints", "version": "0.1"}}})
    post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})


# ---------------------------------------------------------------------------
# 离线样板数据（明确标注“非实时”，用于演示；真实账号接入即替换）
# ---------------------------------------------------------------------------
OFFLINE = {
    "account": {
        "availablePoint": "1280", "accumulativePoint": "5640",
        "currency": "麦享会积分", "currentMouthExpirePoint": "0",
        "lastMouthExpirePoint": "420", "nextMouthExpirePoint": "300",
        "expiredPoint": "120", "frozenPoint": "0", "usedPoint": "3860",
    },
    "lottery": {
        "activityName": "麦麦积分抽奖", "drawPoint": "24",
        "availablePoint": "1280",
        "drawDecision": {"resourceEligible": True, "reason": "",
                         "nextConsumption": {"points": "24", "chances": 53}},
        "prizes": [
            {"name": "下单立减3元券", "typeText": "优惠券"},
            {"name": "下单立减2元券", "typeText": "优惠券"},
            {"name": "麦辣三件套5折券", "typeText": "优惠券"},
            {"name": "板烧三件套5折券", "typeText": "优惠券"},
            {"name": "甜辣小食组合5折券", "typeText": "优惠券"},
            {"name": "免费吉士堡券", "typeText": "实物"},
        ],
    },
    "products": [
        {"spuName": "麦辣鸡腿堡免费券", "spuId": 9001, "point": "1500",
         "price": "21.0", "catName": "商品券"},
        {"spuName": "薯条买一送一券", "spuId": 9002, "point": "800",
         "price": "12.0", "catName": "商品券"},
        {"spuName": "免费吉士堡券", "spuId": 9003, "point": "600",
         "price": "13.0", "catName": "商品券"},
        {"spuName": "10元现金抵用券", "spuId": 9004, "point": "1000",
         "price": "10.0", "catName": "商品券"},
        {"spuName": "麦旋风买一送一券", "spuId": 9005, "point": "500",
         "price": "14.0", "catName": "商品券"},
        {"spuName": "中杯可乐免费券", "spuId": 9006, "point": "300",
         "price": "9.0", "catName": "商品券"},
    ],
}


# ---------------------------------------------------------------------------
# 计算逻辑（本地化，MCP 只取数）
# ---------------------------------------------------------------------------
def to_int(v):
    try:
        return int(str(v))
    except Exception:
        return 0


def analyze(account, lottery, products):
    avail = to_int(account.get("availablePoint"))
    acc = to_int(account.get("accumulativePoint"))
    used = to_int(account.get("usedPoint"))
    frozen = to_int(account.get("frozenPoint"))
    cur_exp = to_int(account.get("currentMouthExpirePoint"))
    next_exp = to_int(account.get("nextMouthExpirePoint"))
    last_exp = to_int(account.get("lastMouthExpirePoint"))

    # 过期预警：优先提示下月即将过期的积分
    expire_warn = []
    if next_exp > 0:
        expire_warn.append(("下月将过期", next_exp))
    if cur_exp > 0:
        expire_warn.append(("本月将过期", cur_exp))
    if last_exp > 0:
        expire_warn.append(("上月已过期(未用)", last_exp))

    # 抽奖评估
    draw_point = to_int(lottery.get("drawPoint"))
    lot_avail = to_int(lottery.get("availablePoint"))
    if draw_point > 0:
        max_draws = lot_avail // draw_point
    else:
        max_draws = 0
    prizes = lottery.get("prizes", []) or []

    # 兑换性价比：仅取积分价 > 0 的商品，按 价值密度(分/百积分) 排序
    rows = []
    for p in products:
        pt = to_int(p.get("point"))
        pr = float(str(p.get("price", "0") or "0"))
        if pt > 0 and pr > 0:
            density = round(pr / pt * 100, 2)  # 每 100 积分可兑换的“元价值”
            rows.append({
                "name": p.get("spuName", ""),
                "spuId": p.get("spuId"),
                "point": pt, "price": pr, "cat": p.get("catName", ""),
                "density": density,
            })
    rows.sort(key=lambda x: x["density"], reverse=True)

    # 建议
    advice = []
    if next_exp > 0:
        advice.append(f"你有 {next_exp} 积分将于下月过期，建议优先兑换高价值密度的券，避免作废。")
    if max_draws > 0:
        top = prizes[0]["name"] if prizes else "优惠券"
        advice.append(f"当前可抽 {max_draws} 次（每次耗 {draw_point} 积分），奖池含「{top}」等，可小试。")
    if rows:
        best = rows[0]
        advice.append(f"性价比最高：「{best['name']}」每 100 积分≈{best['density']} 元，建议优先兑换。")
    if not advice:
        advice.append("暂无需要紧急处理的积分，保持日常签到积累即可。")

    return {
        "avail": avail, "acc": acc, "used": used, "frozen": frozen,
        "currency": account.get("currency", "积分"),
        "expire_warn": expire_warn, "max_draws": max_draws,
        "draw_point": draw_point, "prizes": prizes, "rows": rows,
        "advice": advice,
    }


# ---------------------------------------------------------------------------
# HTML 渲染（自包含，无外部依赖）
# ---------------------------------------------------------------------------
def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def render(a, live):
    tag = "实时数据" if live else "离线演示数据（非实时 · 仅供展示）"
    rows_html = ""
    if a["rows"]:
        for i, r in enumerate(a["rows"], 1):
            medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}."))
            rows_html += f"""<tr>
              <td class="rank">{medal}</td>
              <td>{esc(r['name'])}</td>
              <td>{r['point']:,}</td>
              <td>¥{r['price']}</td>
              <td><b>{r['density']}</b></td>
              <td>{esc(r['cat'])}</td></tr>"""
    else:
        rows_html = '<tr><td colspan="6" class="muted">当前积分商城无可用积分兑换商品（或需指定类目）</td></tr>'

    warn_html = ""
    if a["expire_warn"]:
        items = "".join(
            f'<li><span class="badge">⚠ {esc(w[0])}</span> <b>{w[1]:,}</b> 积分</li>'
            for w in a["expire_warn"])
        warn_html = f'<div class="alert">🔥 过期预警<ul>{items}</ul></div>'
    else:
        warn_html = '<div class="ok">✅ 近期无积分过期风险</div>'

    prizes_html = "".join(
        f'<span class="chip">{esc(p.get("name",""))}</span>' for p in a["prizes"]) or '<span class="muted">无</span>'

    advice_html = "".join(f"<li>{esc(x)}</li>" for x in a["advice"])

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>麦麦积分精算师 · 看板</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
 background:linear-gradient(135deg,#fff7e6,#ffe9c7);color:#2b2b2b;padding:20px}}
.wrap{{max-width:760px;margin:0 auto}}
.tag{{display:inline-block;font-size:12px;padding:3px 10px;border-radius:12px;
 background:#ffc72c;color:#27251f;font-weight:700;margin-bottom:8px}}
h1{{font-size:24px;color:#da291c}}
.sub{{color:#7a7a7a;font-size:13px;margin-bottom:16px}}
.card{{background:#fff;border-radius:16px;padding:18px;margin:14px 0;
 box-shadow:0 6px 18px rgba(218,41,28,.08)}}
.big{{font-size:40px;font-weight:800;color:#da291c}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap}}
.kpi{{flex:1;min-width:120px;background:#fffaf0;border-radius:12px;padding:12px;text-align:center}}
.kpi .n{{font-size:22px;font-weight:700;color:#27251f}}
.kpi .l{{font-size:12px;color:#9a9a9a}}
.alert{{background:#fff3f0;border-left:5px solid #da291c;padding:12px 14px;border-radius:8px}}
.ok{{background:#eafaf0;border-left:5px solid #2e9e5b;padding:12px 14px;border-radius:8px}}
.alert ul{{margin:8px 0 0 18px}}
.badge{{background:#da291c;color:#fff;padding:1px 8px;border-radius:10px;font-size:12px}}
table{{width:100%;border-collapse:collapse;margin-top:6px;font-size:14px}}
th,td{{padding:8px 6px;border-bottom:1px solid #f0e6d2;text-align:left}}
th{{color:#9a9a9a;font-weight:600;font-size:12px}}
.rank{{font-size:16px}}
.chip{{display:inline-block;background:#fff3d6;color:#8a6410;border-radius:10px;
 padding:3px 9px;margin:3px;font-size:12px}}
.advice{{background:#fff;border-radius:12px;padding:12px 16px}}
.advice li{{margin:6px 0 6px 18px}}
.muted{{color:#9a9a9a}}
.foot{{text-align:center;color:#9a9a9a;font-size:12px;margin-top:18px}}
</style></head><body><div class="wrap">
<div class="tag">{esc(tag)}</div>
<h1>🪙 麦麦积分精算师</h1>
<div class="sub">基于麦当劳官方 MCP 只读数据 · 积分体检 / 过期预警 / 抽奖评估 / 兑换性价比</div>

<div class="card">
  <div class="kpis">
    <div class="kpi"><div class="n">{a['avail']:,}</div><div class="l">可用积分</div></div>
    <div class="kpi"><div class="n">{a['acc']:,}</div><div class="l">累计积分</div></div>
    <div class="kpi"><div class="n">{a['used']:,}</div><div class="l">已用积分</div></div>
    <div class="kpi"><div class="n">{a['frozen']:,}</div><div class="l">冻结积分</div></div>
  </div>
</div>

{warn_html}

<div class="card">
  <h3>🎰 抽奖评估</h3>
  <p>每次消耗 <b>{a['draw_point']}</b> 积分，当前可抽 <b style="color:#da291c">{a['max_draws']}</b> 次。</p>
  <p class="muted" style="margin-top:6px">奖池：</p>
  <div>{prizes_html}</div>
</div>

<div class="card">
  <h3>🏆 兑换性价比排行（每 100 积分≈？元）</h3>
  <table><thead><tr><th>排名</th><th>商品</th><th>积分价</th><th>面值</th><th>密度</th><th>类目</th></tr></thead>
  <tbody>{rows_html}</tbody></table>
</div>

<div class="card advice">
  <h3>💡 智能建议</h3>
  <ul>{advice_html}</ul>
</div>

<div class="foot">麦麦派对官 · 积分精算模块 | 数据来源：麦当劳官方 MCP（只读）| 不存储账号凭证</div>
</div></body></html>"""


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="麦麦积分精算师")
    ap.add_argument("--offline", action="store_true", help="使用内置离线样板数据（无需 Token）")
    ap.add_argument("--html", default="assets/points_dashboard.html", help="看板 HTML 输出路径")
    args = ap.parse_args()

    if args.offline:
        a = analyze(OFFLINE["account"], OFFLINE["lottery"], OFFLINE["products"])
        html_out = render(a, live=False)
        print("[离线模式] 已使用内置样板数据（非实时）")
    else:
        if not TOKEN:
            sys.exit("缺少环境变量 MCD_MCP_TOKEN（请用 --offline 演示，或用环境变量传入真实 Token）")
        init()
        acc = call("query-my-account", {})
        acc_data = (acc.get("data") if isinstance(acc, dict) else {}) or {}
        lot = call("query-lottery-info", {})
        lot_data = (lot.get("data") if isinstance(lot, dict) else {}) or {}
        mall = call("mall-points-products", {})
        mall_data = mall.get("data") if isinstance(mall, dict) else mall
        if not isinstance(mall_data, list):
            mall_data = []
        a = analyze(acc_data, lot_data, mall_data)
        html_out = render(a, live=True)
        print("[实时模式] 已读取麦当劳官方 MCP 数据")

    Path(args.html).parent.mkdir(parents=True, exist_ok=True)
    Path(args.html).write_text(html_out, encoding="utf-8")
    print("看板已生成 ->", args.html)


if __name__ == "__main__":
    main()
