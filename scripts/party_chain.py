#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦麦派对官 - 真实 MCP 链路编排脚本（端到端只读，绝不下单）。

读取环境变量 MCD_MCP_TOKEN，调用麦当劳官方 MCP（mcp.mcd.cn）真实跑通：
  mall-points-products（取派对 spu）
    → query-party-city（城市）
    → query-party-store（门店）
    → query-party-store-date（日期）
    → query-party-store-session（场次）
并将结果映射为 party_planner.py 的入参 schema，写出 real_data.json，
再直接渲染 assets/real_party_plan.html 真实策划单。

用法：
  MCD_MCP_TOKEN=xxxx python party_chain.py \
      --party "奇妙生日派对" --city "上海" \
      --out real_data.json --html assets/real_party_plan.html

安全：仅查询，不调用 party-order-create；Token 仅从环境变量读取，不写盘。
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
            return body, None
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", "replace"), e.code


# 真实捕获快照：来自 2026-10-15 23:3x 对麦当劳官方 MCP 的成功只读探测返回。
# 仅用于离线演示（Token 失效时），非实时数据。
OFFLINE_SNAPSHOT = {
    "city": "安康",
    "store": {"name": "麦当劳安康时代购物广场餐厅", "storeCode": "1960713"},
    "date": "2026-11-08",
    "session": {"label": "12:00-13:30", "sessionId": "36888219"},
    "theme": "麦当劳奇妙生日派对",
    "guests": 5,
    "meals": [
        {"name": "派对基础费用（12:00-13:30）", "price": 50.0, "qty": 1}
    ],
    "note": ("本单为 2026-10-15 捕获的麦当劳 MCP 真实返回快照（非实时），用于离线演示；"
             "实时数据请用有效 Token 运行："
             "MCD_MCP_TOKEN=xxx python party_chain.py --party '奇妙生日派对' --city '上海'"),
}



def call(name, args):
    raw, code = post({"jsonrpc": "2.0", "id": 99, "method": "tools/call",
                     "params": {"name": name, "arguments": args}})
    if code == 401:
        sys.exit("[fail] 401 未授权：Token 可能已失效，请到 open.mcd.cn/mcp 重新生成后再试。")
    res = json.loads(raw) if raw.strip().startswith("{") else {"result": {}}
    r = res.get("result", {})
    sc = r.get("structuredContent")
    if sc is not None:
        return sc
    txt = (r.get("content") or [{}])[0].get("text", "")
    i = txt.find("## Original Response")
    if i >= 0:
        m = re.search(r"\{.*\}", txt[i:], re.S)
        if m:
            return json.loads(m.group(0))
    return {"_raw": txt[:400]}


def main():
    ap = argparse.ArgumentParser(description="麦麦派对官 - 真实 MCP 链路编排")
    ap.add_argument("--party", default="奇妙生日派对", help="派对主题关键词（匹配 spuName）")
    ap.add_argument("--city", default=None, help="目标城市名（模糊匹配），不填则取第一个城市")
    ap.add_argument("--out", default="real_data.json", help="中间数据 JSON 输出路径")
    ap.add_argument("--html", default="assets/real_party_plan.html", help="真实策划单 HTML 输出路径")
    ap.add_argument("--offline", action="store_true",
                    help="使用内置真实捕获快照离线渲染（无需 Token，非实时）")
    args = ap.parse_args()

    if args.offline:
        data = OFFLINE_SNAPSHOT
        Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        print(f"[offline] 已写出快照数据：{args.out}")
        sys.path.insert(0, str(Path(__file__).parent))
        from party_planner import build_html
        Path(args.html).parent.mkdir(parents=True, exist_ok=True)
        Path(args.html).write_text(build_html(data), encoding="utf-8")
        print(f"[offline] 已生成离线策划单：{args.html}")
        return

    if not TOKEN:
        sys.exit("缺少环境变量 MCD_MCP_TOKEN（请通过环境变量传入，勿写盘）")

    # 初始化会话
    post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                     "clientInfo": {"name": "party_chain", "version": "0.1"}}})
    post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    # STEP0：取派对 spu
    mall = call("mall-points-products", {})
    party = [p for p in mall.get("data", [])
             if args.party in str(p.get("spuName", ""))]
    if not party:
        all_party = [p for p in mall.get("data", [])
                     if "派对" in str(p.get("spuName", ""))]
        print("[warn] 未匹配到『%s』，可选派对：" % args.party)
        for p in all_party[:10]:
            print("   -", p.get("spuId"), p.get("spuName"))
        sys.exit(1)
    spu = party[0]
    spu_id = spu.get("spuId")
    spu_name = spu.get("spuName")
    print(f"[step0] 选用派对 spuId={spu_id} {spu_name}")

    # STEP1：城市
    c = call("query-party-city", {"spuId": spu_id})
    cities = c.get("data", [])
    if not c.get("success") or not cities:
        sys.exit("[fail] query-party-city: " + str(c.get("message")))
    if args.city:
        target = next((x for x in cities
                       if args.city in str(x.get("name", ""))), None)
        if not target:
            print("[warn] 未找到城市『%s』，改用第一个城市" % args.city)
            target = cities[0]
    else:
        target = cities[0]
    city_name = target.get("name")
    code = str(target.get("code"))
    lat = target.get("latitude")
    lon = target.get("longitude")
    print(f"[step1] 城市={city_name} code={code}")

    # STEP2：门店
    s = call("query-party-store",
             {"code": code, "latitude": lat, "longitude": lon, "spuId": spu_id})
    stores = s.get("data", [])
    if not s.get("success") or not stores:
        sys.exit("[fail] query-party-store: " + str(s.get("message")))
    store0 = stores[0]
    store_code = store0.get("storeCode") or store0.get("code")
    store_name = store0.get("name") or store0.get("storeName") or f"门店{store_code}"
    print(f"[step2] 门店={store_name} storeCode={store_code}")

    # STEP3：日期
    dt = call("query-party-store-date", {"spuId": spu_id, "storeCode": store_code})
    dates = dt.get("data", [])
    if not dt.get("success") or not dates:
        sys.exit("[fail] query-party-store-date: " + str(dt.get("message")))
    d0 = dates[0]
    date_str = d0.get("dateStr") or d0.get("date") or d0.get("day")
    print(f"[step3] 日期={date_str}")

    # STEP4：场次
    ss = call("query-party-store-session",
              {"spuId": spu_id, "storeCode": store_code, "dateStr": date_str})
    sessions = ss.get("data", [])
    if not ss.get("success") or not sessions:
        sys.exit("[fail] query-party-store-session: " + str(ss.get("message")))
    sess0 = sessions[0]
    sid = sess0.get("id")
    t_start = sess0.get("timeStart") or sess0.get("startTime") or ""
    t_end = sess0.get("timeEnd") or sess0.get("endTime") or ""
    label = f"{t_start}-{t_end}" if (t_start and t_end) else str(sid)
    pmin = sess0.get("partyMin") or sess0.get("peopleMin") or 0
    pmax = sess0.get("partyMax") or sess0.get("peopleMax") or 0
    # 价格单位：场次级为「分」，需换算成元
    raw_price = sess0.get("price") or 0
    price_yuan = round(raw_price / 100.0, 2) if raw_price > 1000 else raw_price
    left = sess0.get("leftNum") or sess0.get("remain") or "?"
    print(f"[step4] 场次 id={sid} {label} 成团 {pmin}-{pmax}人 单价¥{price_yuan} 余位{left}")

    # 组装为 party_planner.py 的入参 schema
    data = {
        "city": city_name,
        "store": {"name": store_name, "storeCode": str(store_code)},
        "date": str(date_str),
        "session": {"label": label, "sessionId": str(sid)},
        "theme": spu_name,
        "guests": int(pmin) if pmin else 0,
        "meals": [
            {"name": f"派对基础费用（{label}）", "price": float(price_yuan), "qty": 1}
        ],
        "note": (f"数据来源：麦当劳官方 MCP 实时返回（spuId={spu_id}）。"
                 f"成团人数 {pmin}-{pmax} 人，当前余位 {left}。"
                 f"实际价格、库存与可约场次以官方实时返回为准；"
                 f"本单为策划参考，下单需用户确认后由 party-order-create 执行。"),
    }

    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print(f"[ok] 已写出中间数据：{args.out}")

    # 直接复用 party_planner 渲染 HTML
    sys.path.insert(0, str(Path(__file__).parent))
    from party_planner import build_html
    Path(args.html).parent.mkdir(parents=True, exist_ok=True)
    Path(args.html).write_text(build_html(data), encoding="utf-8")
    print(f"[ok] 已生成真实策划单：{args.html}")


if __name__ == "__main__":
    main()
