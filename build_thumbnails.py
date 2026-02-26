#!/usr/bin/env python3
"""
缩略图脚本：
1. 创建 main/（存放大图）和 thumbs/（存放 350x350 缩略图），图片格式统一为 JPG
2. 将项目根目录下的 nailart*.jpg / nailart*.png 转为 JPG 写入 main/
3. 为 main/ 中每张图生成 350x350 的 JPG 缩略图到 thumbs/
4. 自动更新 explore_data.json 中的 imageURL、thumbnailURL（统一为 .jpg 地址）

使用前请安装依赖: pip install Pillow
运行: python3 build_thumbnails.py
"""
import json
import os
import re
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
BASE_URL = "https://raw.githubusercontent.com/JiangAogo/NailArtAssets/main"


def ensure_dirs():
    MAIN_DIR.mkdir(exist_ok=True)
    THUMBS_DIR.mkdir(exist_ok=True)
    print(f"已确保目录: {MAIN_DIR.name}/, {THUMBS_DIR.name}/")


def save_as_jpg(im: Image.Image, dest_path: Path, quality: int = 85):
    """将 PIL 图片以 JPG 格式保存。"""
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.save(dest_path, format="JPEG", quality=quality, optimize=True)


def collect_and_copy_sources():
    """从项目根目录收集 nailart*.jpg / nailart*.png，统一转为 JPG 写入 main/。"""
    pattern = re.compile(r"^nailart(\d+)\.(jpg|jpeg|png)$", re.I)
    converted = 0
    for f in SCRIPT_DIR.iterdir():
        if not f.is_file():
            continue
        m = pattern.match(f.name)
        if not m:
            continue
        num = m.group(1)
        dest = MAIN_DIR / f"nailart{num}.jpg"
        if dest.resolve() == f.resolve():
            continue
        with Image.open(f) as im:
            save_as_jpg(im, dest)
        converted += 1
        print(f"  大图转 JPG: {f.name} -> main/nailart{num}.jpg")
    # 将 main/ 中已有的 PNG 也转为 JPG 并删除原 PNG
    for f in list(MAIN_DIR.iterdir()):
        if not f.is_file() or f.suffix.lower() != ".png":
            continue
        m = pattern.match(f.name)
        if not m:
            continue
        num = m.group(1)
        dest = MAIN_DIR / f"nailart{num}.jpg"
        with Image.open(f) as im:
            save_as_jpg(im, dest)
        f.unlink()
        converted += 1
        print(f"  main 内转 JPG: {f.name} -> main/nailart{num}.jpg")
    if converted:
        print(f"共处理 {converted} 张大图到 main/（统一 JPG）")
    else:
        print("未发现需要处理的 nailart 图片（可能已在 main/ 且为 JPG）")


def make_thumbnail(src_path: Path, dest_path: Path, size: tuple):
    """将图片缩放为 size 并保存为 JPG 到 dest_path。"""
    with Image.open(src_path) as im:
        im.thumbnail(size, Image.Resampling.LANCZOS)
        save_as_jpg(im, dest_path)


def build_thumbnails():
    """为 main/ 中每张图生成 350x350 的 JPG 缩略图到 thumbs/，序号与 id 一致。"""
    pattern = re.compile(r"^nailart(\d+)\.(jpg|jpeg)$", re.I)
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
        thumb_name = f"nailart{num}.jpg"
        dest = THUMBS_DIR / thumb_name
        make_thumbnail(f, dest, THUMB_SIZE)
        entries.append((num, f"nailart{num}.jpg", thumb_name))
        print(f"  缩略图: main/{f.name} -> thumbs/{thumb_name}")
    entries.sort(key=lambda x: x[0])
    print(f"共生成 {len(entries)} 张缩略图（统一 JPG）")
    return entries


def update_json(entries: list):
    """
    更新 explore_data.json：imageURL、thumbnailURL 统一为 .jpg 地址。
    - heroImage.imageURL: main/nailart0.jpg
    - items[].imageURL: main/nailart{id}.jpg
    - items[].thumbnailURL: thumbs/nailart{id}.jpg
    - 若 main/ 中新增了图片，会为对应 id 在 items 中追加新条目。
    """
    by_num = {e[0]: (e[1], e[2]) for e in entries}

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if 0 in by_num:
        data["heroImage"]["imageURL"] = f"{BASE_URL}/main/nailart0.jpg"

    existing_ids = {int(item["id"]) for item in data["items"]}
    # 为 main/ 中新增的图片在 items 里追加条目
    for n in sorted(by_num.keys()):
        if n not in existing_ids:
            data["items"].append({
                "id": str(n),
                "imageURL": f"{BASE_URL}/main/nailart{n}.jpg",
                "thumbnailURL": f"{BASE_URL}/thumbs/nailart{n}.jpg",
            })
            existing_ids.add(n)

    # 按 id 排序，保证顺序一致
    data["items"].sort(key=lambda item: int(item["id"]))

    for item in data["items"]:
        n = int(item["id"])
        if n not in by_num:
            continue
        item["imageURL"] = f"{BASE_URL}/main/nailart{n}.jpg"
        item["thumbnailURL"] = f"{BASE_URL}/thumbs/nailart{n}.jpg"

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新 {JSON_PATH} 中的 imageURL 与 thumbnailURL（统一 .jpg）")


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
