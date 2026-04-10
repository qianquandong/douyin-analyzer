import json
import os
import re
from urllib.parse import parse_qs, urlparse

import requests
import yt_dlp

from .config import DOUYIN_HEADERS


def _normalize_url(url: str) -> str:
    """将各种抖音链接格式转换为 yt-dlp 支持的标准格式。"""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "modal_id" in qs:
        video_id = qs["modal_id"][0]
        return f"https://www.douyin.com/video/{video_id}"
    if re.search(r"/video/\d+", url):
        return url
    return url


def _extract_video_id_from_url(url: str) -> str:
    """从标准化后的URL中提取视频ID。"""
    match = re.search(r"/video/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"modal_id=(\d+)", url)
    if match:
        return match.group(1)
    return ""


def _download_via_api(video_id: str, output_dir: str) -> dict | None:
    """通过抖音网页API直接下载视频，不需要cookies。"""
    api_url = f"https://www.iesdouyin.com/share/video/{video_id}"
    headers = {
        "User-Agent": DOUYIN_HEADERS["User-Agent"],
        "Referer": "https://www.douyin.com/",
    }

    try:
        resp = requests.get(api_url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    # 尝试从页面中提取视频信息
    match = re.search(r'window\._ROUTER_DATA\s*=\s*({.*?})\s*</script>', resp.text, re.DOTALL)
    if not match:
        # 尝试另一种模式
        match = re.search(r'"playApi"\s*:\s*"(https?://[^"]+)"', resp.text)
        if match:
            video_url = match.group(1).replace("\\u002F", "/")
            return _download_direct_url(video_url, video_id, output_dir, headers)
        return None

    try:
        data = json.loads(match.group(1))
        # 遍历查找视频URL
        data_str = json.dumps(data)
        play_match = re.search(r'"playApi"\s*:\s*"(https?://[^"]+)"', data_str)
        if play_match:
            video_url = play_match.group(1).replace("\\u002F", "/")
            return _download_direct_url(video_url, video_id, output_dir, headers)
    except json.JSONDecodeError:
        pass

    return None


def _download_direct_url(video_url: str, video_id: str, output_dir: str, headers: dict) -> dict | None:
    """直接下载视频URL。"""
    video_path = os.path.join(output_dir, "video.mp4")
    try:
        resp = requests.get(video_url, headers=headers, timeout=60, stream=True)
        resp.raise_for_status()
        with open(video_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return {
            "video_path": video_path,
            "title": f"抖音视频_{video_id}",
            "video_id": video_id,
            "duration": 0,  # API方式无法直接获取时长，后续从视频文件读取
        }
    except requests.RequestException:
        return None


def _get_duration_from_file(video_path: str) -> float:
    """从视频文件读取时长。"""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", video_path],
            capture_output=True, text=True, timeout=10,
        )
        info = json.loads(result.stdout)
        return float(info.get("format", {}).get("duration", 0))
    except Exception:
        return 0


def download_video(url: str, output_dir: str, cookies_from: str = "chrome") -> dict:
    """
    下载抖音视频。优先用yt-dlp，失败后回退到API方式。

    Args:
        url: 抖音视频链接
        output_dir: 输出目录
        cookies_from: 从哪个浏览器读取cookies（chrome/firefox/edge/safari）

    返回:
        dict: {video_path, title, video_id, duration}
    """
    os.makedirs(output_dir, exist_ok=True)
    url = _normalize_url(url)
    video_id = _extract_video_id_from_url(url)

    # 方法1: yt-dlp（带cookies）
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "video.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "http_headers": DOUYIN_HEADERS,
        "no_warnings": True,
        "quiet": True,
        "no_color": True,
        "merge_output_format": "mp4",
        "cookiesfrombrowser": (cookies_from,),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        video_path = os.path.join(output_dir, "video.mp4")
        if not os.path.exists(video_path):
            for f in os.listdir(output_dir):
                if f.startswith("video."):
                    video_path = os.path.join(output_dir, f)
                    break

        return {
            "video_path": video_path,
            "title": info.get("title", "未知标题"),
            "video_id": str(info.get("id", video_id or "unknown")),
            "duration": info.get("duration", 0),
        }
    except yt_dlp.utils.DownloadError:
        pass

    # 方法2: yt-dlp（不带cookies）
    ydl_opts.pop("cookiesfrombrowser", None)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        video_path = os.path.join(output_dir, "video.mp4")
        if not os.path.exists(video_path):
            for f in os.listdir(output_dir):
                if f.startswith("video."):
                    video_path = os.path.join(output_dir, f)
                    break

        return {
            "video_path": video_path,
            "title": info.get("title", "未知标题"),
            "video_id": str(info.get("id", video_id or "unknown")),
            "duration": info.get("duration", 0),
        }
    except yt_dlp.utils.DownloadError:
        pass

    # 方法3: 直接API下载
    if video_id:
        result = _download_via_api(video_id, output_dir)
        if result and os.path.exists(result["video_path"]):
            # 补充时长信息
            if result["duration"] == 0:
                result["duration"] = _get_duration_from_file(result["video_path"])
            return result

    raise RuntimeError(
        "视频下载失败，所有方式均未成功。\n"
        "请尝试：\n"
        "  1. 在浏览器中打开 douyin.com 并访问该视频\n"
        "  2. 使用浏览器扩展导出 cookies.txt 文件\n"
        "  3. 检查链接是否正确且视频为公开视频"
    )
