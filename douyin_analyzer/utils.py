import os
import re
import shutil
import subprocess

from PIL import Image

from .config import MAX_IMAGE_SIZE_BYTES


def ensure_ffmpeg():
    """检查ffmpeg是否安装。"""
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg 未安装。请先安装：\n"
            "  macOS:   brew install ffmpeg\n"
            "  Ubuntu:  sudo apt install ffmpeg\n"
            "  Windows: https://ffmpeg.org/download.html"
        )


def sanitize_filename(name: str) -> str:
    """移除文件名中的特殊字符。"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip().replace(" ", "_")
    return name[:100] if name else "untitled"


def format_timestamp(seconds: float) -> str:
    """将秒数转换为 MM:SS 格式。"""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"


def resize_image_if_needed(image_path: str) -> str:
    """如果图片超过大小限制，缩放图片。返回（可能更新后的）路径。"""
    file_size = os.path.getsize(image_path)
    if file_size <= MAX_IMAGE_SIZE_BYTES:
        return image_path

    img = Image.open(image_path)
    quality = 85
    while file_size > MAX_IMAGE_SIZE_BYTES and quality > 20:
        # 缩小尺寸
        if quality == 85:
            ratio = (MAX_IMAGE_SIZE_BYTES / file_size) ** 0.5
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        img.save(image_path, "JPEG", quality=quality)
        file_size = os.path.getsize(image_path)
        quality -= 10

    return image_path


def extract_video_id(url: str) -> str:
    """从抖音URL中提取视频ID。"""
    # 匹配 /video/1234567890 格式
    match = re.search(r"/video/(\d+)", url)
    if match:
        return match.group(1)
    # 匹配 modal_id=1234567890 参数
    match = re.search(r"modal_id=(\d+)", url)
    if match:
        return match.group(1)
    # 短链接使用hash
    match = re.search(r"douyin\.com/([A-Za-z0-9]+)", url)
    if match:
        return match.group(1)
    return sanitize_filename(url)[-20:]
