#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦麦派对官 - 派对策划单生成器。

读取派对数据(JSON)，生成一份可视化 HTML 策划单，用于演示与归档。

输入 JSON 字段：
{
  "city": "上海",
  "store": {"name": "门店名", "storeCode": "..."},
  "date": "2026-10-25",
  "session": {"label": "上午场 10:00-12:00", "sessionId": "..."},
  "theme": "麦当劳主题生日派对",
  "guests": 10,
  "meals": [{"name": "开心乐园餐", "price": 39.0, "qty": 8}],
  "note": "可选备注"
}

用法：
  python party_planner.py input.json -o output.html
"""
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

try:
    from html import escape
except ImportError:  # pragma: no cover
    def escape(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def build_html(data: dict) -> str:
    meals = data.get("meals", []) or []
    total = sum(float(m.get("price", 0)) * int(m.get("qty", 0)) for m in meals)
    if meals:
        rows = "".join(
            "<tr><td>{name}</td><td>¥{price:.1f}</td><td>x{qty}</td>"
            "<td>¥{sub:.1f}</td></tr>".format(
                name=escape(m.get("name", "")),
                price=float(m.get("price", 0)),
                qty=int(m.get("qty", 0)),
                sub=float(m.get("price", 0)) * int(m.get("qty", 0)),
            )
            for m in meals
        )
    else:
        rows = '<tr><td colspan="4">（未选择餐品）</td></tr>'

    store = data.get("store", {}) or {}
    session = data.get("session", {}) or {}
    gen = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>麦麦派对策划单</title>
<style>
  body{{font-family:-apple-system,"Microsoft YaHei",sans-serif;background:#fff7e6;color:#3a2a12;margin:0;padding:24px}}
  .card{{max-width:720px;margin:0 auto;background:#fff;border-radius:16px;padding:28px;box-shadow:0 8px 30px rgba(255,160,0,.18)}}
  h1{{color:#e60012;margin:0 0 4px;font-size:24px}}
  .sub{{color:#9a7b4f;font-size:13px;margin-bottom:18px}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:18px}}
  .box{{background:#fff7e6;border-radius:10px;padding:12px 14px}}
  .box .k{{font-size:12px;color:#9a7b4f}}
  .box .v{{font-size:16px;font-weight:700;margin-top:2px}}
  table{{width:100%;border-collapse:collapse;margin-top:6px}}
  th,td{{padding:8px 10px;border-bottom:1px solid #ffe0a3;text-align:left;font-size:14px}}
  th{{color:#e60012}}
  .total{{text-align:right;font-weight:700;font-size:18px;color:#e60012;margin-top:10px}}
  .note{{margin-top:14px;font-size:13px;color:#9a7b4f;line-height:1.6}}
</style>
</head>
<body>
<div class="card">
  <h1>🎉 {escape(data.get('theme', '麦当劳主题派对'))}</h1>
  <div class="sub">麦麦派对官 · 策划单 · 生成于 {gen}</div>
  <div class="grid">
    <div class="box"><div class="k">城市</div><div class="v">{escape(data.get('city', ''))}</div></div>
    <div class="box"><div class="k">门店</div><div class="v">{escape(store.get('name', ''))}</div></div>
    <div class="box"><div class="k">日期</div><div class="v">{escape(data.get('date', ''))}</div></div>
    <div class="box"><div class="k">场次</div><div class="v">{escape(session.get('label', ''))}</div></div>
    <div class="box"><div class="k">人数</div><div class="v">{int(data.get('guests', 0))} 人</div></div>
    <div class="box"><div class="k">门店编码</div><div class="v">{escape(store.get('storeCode', ''))}</div></div>
  </div>
  <table>
    <thead><tr><th>餐品</th><th>单价</th><th>数量</th><th>小计</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="total">预计餐品合计：¥{total:.1f}</div>
  <div class="note">备注：{escape(data.get('note', ''))}<br>
  说明：实际价格、库存与可约场次以麦当劳官方 MCP 实时返回为准；本单为策划参考，下单需用户确认后由 party-order-create 执行。</div>
</div>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser(description="麦麦派对官 - 策划单生成器")
    ap.add_argument("input", help="派对数据 JSON 文件路径")
    ap.add_argument("-o", "--output", default="party_plan.html", help="输出 HTML 路径")
    args = ap.parse_args()

    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"错误：找不到输入文件 {args.input}")
    except json.JSONDecodeError as e:
        sys.exit(f"错误：JSON 解析失败 - {e}")

    Path(args.output).write_text(build_html(data), encoding="utf-8")
    print(f"已生成策划单：{args.output}")


if __name__ == "__main__":
    main()
