#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性探测脚本：验证麦当劳 MCP Token 有效性 + query-party-city 可用性。
Token 仅从环境变量 MCD_MCP_TOKEN 读取，不写入任何文件。
用法：MCD_MCP_TOKEN=xxx python probe_mcp.py
"""
import os
import sys
import json
import urllib.request
import urllib.error

BASE = "https://mcp.mcd.cn"
TOKEN = os.environ.get("MCD_MCP_TOKEN")
if not TOKEN:
    sys.exit("缺少环境变量 MCD_MCP_TOKEN")


def parse(body):
    body = (body or "").strip()
    if body.startswith("{"):
        return json.loads(body)
    last = None
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            chunk = line[5:].strip()
            if chunk and chunk != "[DONE]":
                try:
                    last = json.loads(chunk)
                except Exception:
                    pass
    return last


def post(payload, session_id=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    req.add_header("Authorization", "Bearer " + TOKEN)
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", "replace")
            sid = (resp.headers.get("Mcp-Session-Id")
                   or resp.headers.get("mcp-session-id") or session_id)
            return parse(body), sid
    except urllib.error.HTTPError as e:
        return {"_error": e.code,
                "_body": e.read().decode("utf-8", "replace")[:500]}, session_id
    except Exception as e:  # 网络/超时等
        return {"_error": str(e)}, session_id


print("== 1. initialize ==")
res, sid = post({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
               "clientInfo": {"name": "probe", "version": "0.1"}},
})
print(json.dumps(res, ensure_ascii=False)[:600])
if isinstance(res, dict) and res.get("_error"):
    print("initialize 失败，终止。")
    sys.exit(1)

print("\n== 2. notifications/initialized ==")
post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, sid)

print("\n== 3. tools/list ==")
res, sid = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, sid)
tools = (res.get("result") or {}).get("tools", []) if isinstance(res, dict) else []
print("工具数量:", len(tools))
for t in tools[:8]:
    print("  -", t.get("name"))

print("\n== 4. tools/call: query-party-city ==")
res, sid = post({
    "jsonrpc": "2.0", "id": 3, "method": "tools/call",
    "params": {"name": "query-party-city", "arguments": {}},
}, sid)
print(json.dumps(res, ensure_ascii=False)[:1500])
