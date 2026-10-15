#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成麦麦派对官演示用模拟数据，写入 demo_data.json。

注意：仅为演示 / 测试用途。正式数据须来自麦当劳官方 MCP（query-party-* 工具链）。
真实调用时，请用各 query-party-* 工具返回的城市 / 门店 / 日期 / 场次 / 餐品替换本文件内容。
"""
import json
from pathlib import Path

data = {
    "city": "上海",
    "store": {"name": "麦当劳上海徐汇正大乐城餐厅", "storeCode": "DEMO001"},
    "date": "2026-10-25",
    "session": {"label": "上午场 10:00-12:00", "sessionId": "S_AM"},
    "theme": "麦当劳主题生日派对",
    "guests": 10,
    "meals": [
        {"name": "开心乐园餐（含玩具）", "price": 39.0, "qty": 8},
        {"name": "麦辣鸡腿堡套餐", "price": 34.5, "qty": 2},
        {"name": "麦旋风（分享装）", "price": 15.5, "qty": 4},
    ],
    "note": "演示数据（模拟）。真实预约请接入麦当劳官方 MCP。",
}

Path("demo_data.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("已生成 demo_data.json")
