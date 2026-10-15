#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拉取麦当劳 MCP 全部工具列表，并打印所有 party 相关工具的 inputSchema。
Token 仅从环境变量 MCD_MCP_TOKEN 读取。
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
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", "replace")
        sid = (resp.headers.get("Mcp-Session-Id")
               or resp.headers.get("mcp-session-id") or session_id)
        return parse(body), sid


res, sid = post({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
               "clientInfo": {"name": "probe", "version": "0.1"}},
})
post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, sid)
res, sid = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, sid)
tools = (res.get("result") or {}).get("tools", [])

print("TOTAL TOOLS:", len(tools))
print("--- ALL TOOL NAMES ---")
for t in tools:
    print(t.get("name"))

print("\n--- PARTY-RELATED TOOL SCHEMAS ---")
for t in tools:
    if "party" in t.get("name", "").lower():
        print("\n## " + t.get("name"))
        print(json.dumps(t.get("inputSchema", {}), ensure_ascii=False, indent=2))
