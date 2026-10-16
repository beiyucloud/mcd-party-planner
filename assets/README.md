# assets 资源目录

放置参赛演示素材：

- `demo.gif`：由录屏 MP4 经 `scripts/mp4_to_gif.py`（ffmpeg 调色板方案）转换生成的演示动图（360×800，约 13 秒循环）。展示完整链路。注：非参赛必需，且报名 Issue 正文不得含图片。
- `demo.html`：可交互自包含动画演示，浏览器打开即播放，等价替代 GIF。
- `party_plan.html`：由 `scripts/party_planner.py` 生成的策划单样例（可用 `python scripts/demo_data.py && python scripts/party_planner.py demo_data.json -o assets/party_plan.html` 生成）。

> 提交前请确保动图不包含任何个人 Token、手机号或隐私信息。
