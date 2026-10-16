#!/usr/bin/env python3
"""将录屏 MP4 转为高质量且体积可控的 GIF。
依赖：imageio-ffmpeg（自带 ffmpeg 二进制）、pillow、numpy。
用法：python scripts/mp4_to_gif.py <input.mp4> <output.gif> [--width 480] [--fps 12]
"""
import sys
import os
import subprocess
import argparse

import imageio_ffmpeg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=480, help="输出宽度(px)，高度等比")
    ap.add_argument("--fps", type=int, default=12, help="输出帧率")
    args = ap.parse_args()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    w = args.width
    vf = (
        f"fps={args.fps},scale={w}:-1:flags=lanczos,"
        "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
    )
    cmd = [
        ffmpeg, "-y", "-i", args.inp,
        "-vf", vf,
        "-loop", "0",
        args.out,
    ]
    print("ffmpeg:", ffmpeg)
    print("cmd:", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("STDERR:\n", r.stderr[-3000:])
        sys.exit(f"ffmpeg 失败，returncode={r.returncode}")
    size = os.path.getsize(args.out)
    print(f"OK -> {args.out}  ({size/1024/1024:.2f} MB)")
    if size > 10 * 1024 * 1024:
        print("⚠️ 文件 >10MB，建议降低 --width 或 --fps 后重转。")


if __name__ == "__main__":
    main()
