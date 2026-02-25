#!/usr/bin/env python3
"""
缩略图脚本：
1. 创建 main/（存放大图）和 thumbs/（存放 350x350 缩略图）
2. 将项目根目录下的 nailart*.jpg / nailart*.png 复制到 main/
3. 为 main/ 中每张图生成 350x350 缩略图到 thumbs/，文件名与序号一致
4. 自动更新 explore_data.json 中每个 item 的 imageURL、thumbnailURL

使用前请安装依赖: pip install Pillow
运行: python3 build_thumbnails.py
"""
import json
import os
import re
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("请先安装 Pillow: pip install Pillow")
    raise SystemExit(1)

# 配置
SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_DIR = SCRIPT_DIR / "main"
THUMBS_DIR = SCRIPT_DIR / "thumbs"
THUMB_SIZE = (350, 350)
JSON_PATH = SCRIPT_DIR / "explore_data.json"
BASE_URL = "https://raw.githubusercontent.com/JiangAogo/NailArtAssets"


def ensure_dirs():
    MAIN_DIR.mkdir(exist_ok=True)
    THUMBS_DIR.mkdir(exist_ok=True)
    print(f"已确保目录: {MAIN_DIR.name}/, {THUMBS_DIR.name}/")


def collect_and_copy_sources():
    """从项目根目录收集 nailart*.jpg / nailart*.png，复制到 main/。"""
    pattern = re.compile(r"^nailart(\d+)\.(jpg|jpeg|png)$", re.I)
    copied = 0
    for f in SCRIPT_DIR.iterdir():
        if not f.is_file():
            continue
        m = pattern.match(f.name)
        if not m:
            continue
        dest = MAIN_DIR / f.name
        if dest.resolve() == f.resolve():
            continue
        shutil.copy2(f, dest)
        copied += 1
        print(f"  复制大图: {f.name} -> main/")
    if copied:
        print(f"共复制 {copied} 张大图到 main/")
    else:
        print("未在根目录发现新的 nailart 图片（可能已在 main/）")


def make_thumbnail(src_path: Path, dest_path: Path, size: tuple):
    """将图片缩放为 size 并保存到 dest_path。"""
    with Image.open(src_path) as im:
        im = im.convert("RGB") if im.mode in ("RGBA", "P") else im
        im.thumbnail(size, Image.Resampling.LANCZOS)
        # 若目标为 jpg，统一用 RGB 保存
        if dest_path.suffix.lower() in (".jpg", ".jpeg"):
            if im.mode != "RGB":
                im = im.convert("RGB")
        im.save(dest_path, quality=85, optimize=True)


def build_thumbnails():
    """为 main/ 中每张图生成 350x350 缩略图到 thumbs/，序号与文件名一致。"""
    pattern = re.compile(r"^nailart(\d+)\.(jpg|jpeg|png)$", re.I)
    entries = []
    def sort_key(p):
        m = re.search(r"\d+", p.name)
        return (int(m.group(0)), p.name) if m else (0, p.name)

    for f in sorted(MAIN_DIR.iterdir(), key=sort_key):
        if not f.is_file():
            continue
        m = pattern.match(f.name)
        if not m:
            continue
        num = int(m.group(1))
        ext = m.group(2).lower()
        if ext == "jpeg":
            ext = "jpg"
        thumb_name = f"nailart{m.group(1)}.{ext}"
        dest = THUMBS_DIR / thumb_name
        make_thumbnail(f, dest, THUMB_SIZE)
        entries.append((num, f.name, thumb_name))
        print(f"  缩略图: main/{f.name} -> thumbs/{thumb_name}")
    entries.sort(key=lambda x: x[0])
    print(f"共生成 {len(entries)} 张缩略图")
    return entries


def update_json(entries: list):
    """
    根据 main/ 与 thumbs/ 中的实际文件名，更新 explore_data.json：
    - heroImage.imageURL: main 里 nailart0 的 URL
    - items[].imageURL: main 里对应 id 的 URL
    - items[].thumbnailURL: thumbs 里对应 id 的 URL
    序号与 id 一致。
    """
    by_num = {e[0]: (e[1], e[2]) for e in entries}

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # heroImage: 对应 nailart0
    if 0 in by_num:
        main_name, thumb_name = by_num[0]
        data["heroImage"]["imageURL"] = f"{BASE_URL}/main/{main_name}"

    for item in data["items"]:
        n = int(item["id"])
        if n not in by_num:
            continue
        main_name, thumb_name = by_num[n]
        item["imageURL"] = f"{BASE_URL}/main/{main_name}"
        item["thumbnailURL"] = f"{BASE_URL}/thumbs/{thumb_name}"

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新 {JSON_PATH} 中的 imageURL 与 thumbnailURL")


def main():
    os.chdir(SCRIPT_DIR)
    print("=== 缩略图脚本 ===\n")
    ensure_dirs()
    print("\n1. 收集并复制大图到 main/")
    collect_and_copy_sources()
    print("\n2. 生成 350x350 缩略图到 thumbs/")
    entries = build_thumbnails()
    if not entries:
        print("main/ 中无 nailart 图片，跳过 JSON 更新")
        return
    print("\n3. 更新 explore_data.json")
    update_json(entries)
    print("\n完成。")


if __name__ == "__main__":
    main()
