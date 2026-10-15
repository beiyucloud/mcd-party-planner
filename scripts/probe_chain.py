#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读跑通派对完整链路，验证可行性并打印每步真实返回结构。
Token 仅从环境变量 MCD_MCP_TOKEN 读取。仅做查询，绝不下单。
"""
import os
import sys
import json
import re
import urllib.request

BASE = "https://mcp.mcd.cn"
TOKEN = os.environ.get("MCD_MCP_TOKEN")
if not TOKEN:
    sys.exit("缺少环境变量 MCD_MCP_TOKEN")

_session = None


def post(payload):
    global _session
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    req.add_header("Authorization", "Bearer " + TOKEN)
    if _session:
        req.add_header("Mcp-Session-Id", _session)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", "replace")
        _session = (resp.headers.get("Mcp-Session-Id")
                    or resp.headers.get("mcp-session-id") or _session)
        return body


def call(name, args):
    raw = post({"jsonrpc": "2.0", "id": 99, "method": "tools/call",
               "params": {"name": name, "arguments": args}})
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


post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                 "clientInfo": {"name": "chain", "version": "0.1"}}})
post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

print("== STEP0 mall-points-products（取派对 spu）==")
mall = call("mall-points-products", {})
party = [p for p in mall.get("data", []) if "派对" in p.get("spuName", "")]
print("派对类商品数:", len(party))
for p in party[:5]:
    print("  -", p.get("spuId"), p.get("spuName"), "price=", p.get("price"), "status=", p.get("status"))
spu_id = 1779  # 麦当劳奇妙生日派对
print("选用 spuId =", spu_id)

print("\n== STEP1 query-party-city ==")
c = call("query-party-city", {"spuId": spu_id})
print("success=", c.get("success"), "data条数=", len(c.get("data", [])))
if not c.get("success"):
    sys.exit("city 失败：" + str(c.get("message")))
city0 = c["data"][0]
print("city0 keys:", list(city0.keys()))
print("  示例:", city0.get("name"), "code=", city0.get("code"))
code = str(city0["code"])
lat = city0["latitude"]
lon = city0["longitude"]

print("\n== STEP2 query-party-store ==")
s = call("query-party-store", {"code": code, "latitude": lat, "longitude": lon, "spuId": spu_id})
print("success=", s.get("success"), "data条数=", len(s.get("data", [])))
if not s.get("success"):
    sys.exit("store 失败：" + str(s.get("message")))
store0 = s["data"][0]
print("store0 keys:", list(store0.keys()))
print("  示例:", store0)
store_code = store0.get("storeCode") or store0.get("code")

print("\n== STEP3 query-party-store-date ==")
dt = call("query-party-store-date", {"spuId": spu_id, "storeCode": store_code})
print("success=", dt.get("success"), "data条数=", len(dt.get("data", [])))
if not dt.get("success"):
    sys.exit("date 失败：" + str(dt.get("message")))
d0 = dt["data"][0]
print("date0 keys:", list(d0.keys()))
print("  示例:", d0)
date_str = d0.get("dateStr") or d0.get("date") or d0.get("day")

print("\n== STEP4 query-party-store-session ==")
ss = call("query-party-store-session", {"spuId": spu_id, "storeCode": store_code, "dateStr": date_str})
print("success=", ss.get("success"), "data条数=", len(ss.get("data", [])))
if not ss.get("success"):
    sys.exit("session 失败：" + str(ss.get("message")))
sess0 = ss["data"][0]
print("session0 keys:", list(sess0.keys()))
print("  示例:", sess0)

print("\n✅ 派对完整链路（city→store→date→session）只读跑通。")
