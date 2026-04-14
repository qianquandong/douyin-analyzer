import base64
import re
from pathlib import Path

import anthropic

from .config import CLAUDE_MODEL, STAGE1_PROMPT, STAGE2_PROMPT
from .utils import resize_image_if_needed


def create_client(api_key: str) -> anthropic.Anthropic:
    """创建Anthropic API客户端。"""
    return anthropic.Anthropic(api_key=api_key)


def _image_block(image_path: str) -> dict:
    """构造Claude API的图片消息块。"""
    resize_image_if_needed(image_path)
    image_data = base64.standard_b64encode(
        Path(image_path).read_bytes()
    ).decode("utf-8")
    suffix = Path(image_path).suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": image_data,
        },
    }


def stage1_describe_frame(
    client: anthropic.Anthropic, image_path: str, duration: float
) -> str:
    """
    第一步：为单张关键帧生成视频画面描述词（中文，可还原画面）。

    Args:
        image_path: 关键帧图片路径
        duration: 镜头时长（秒）
    返回:
        str: 画面描述词（中文纯文字）
    """
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    _image_block(image_path),
                    {
                        "type": "text",
                        "text": STAGE1_PROMPT.format(duration=round(duration, 1)),
                    },
                ],
            }
        ],
    )
    return message.content[0].text.strip()


def stage2_generate_prompts(
    client: anthropic.Anthropic,
    shot_descriptions: list[str],
    style_template: str,
) -> list[str]:
    """
    第二步：基于第一步的全部画面描述，统一风格生成最终的中文 AI 提示词。

    Args:
        shot_descriptions: 每个镜头的画面描述词（第一步产出）
        style_template: 统一风格模板字符串
    返回:
        list[str]: 每个镜头的最终中文 AI 提示词
    """
    shot_list = "\n\n".join(
        f"镜头{i + 1}：{desc}" for i, desc in enumerate(shot_descriptions)
    )

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": STAGE2_PROMPT.format(
                    n=len(shot_descriptions),
                    style=style_template,
                    shot_list=shot_list,
                ),
            }
        ],
    )

    raw = message.content[0].text
    return _parse_stage2_output(raw, expected=len(shot_descriptions))


def _parse_stage2_output(text: str, expected: int) -> list[str]:
    """解析第二步返回的分镜提示词列表。"""
    # 按 "## 镜头N" 分段
    parts = re.split(r"##\s*镜头\s*\d+\s*\n", text)
    # 第一段是前言，跳过
    prompts = [p.strip() for p in parts[1:] if p.strip()]
    # 若数量不匹配，用原文补齐/截断
    if len(prompts) < expected:
        prompts += [""] * (expected - len(prompts))
    return prompts[:expected]


def analyze_all_frames(
    client: anthropic.Anthropic,
    frame_items: list[dict],
    style_template: str,
    progress_callback=None,
) -> list[dict]:
    """
    完整的两步分析流程。

    Args:
        frame_items: [{"frame_path": "...", "duration": 秒}, ...]
        style_template: 风格模板
        progress_callback: 可选回调 fn(i, n, stage_name)
    返回:
        list[dict]: [{"frame_path", "description", "prompt", "raw"}]
    """
    # ── Stage 1：逐帧生成画面描述词 ──
    descriptions = []
    n = len(frame_items)
    for i, item in enumerate(frame_items, 1):
        if progress_callback:
            progress_callback(i, n, "stage1")
        desc = stage1_describe_frame(client, item["frame_path"], item["duration"])
        descriptions.append(desc)

    # ── Stage 2：统一风格批量生成最终提示词 ──
    if progress_callback:
        progress_callback(0, 1, "stage2")
    final_prompts = stage2_generate_prompts(client, descriptions, style_template)

    # 组装结果
    results = []
    for item, desc, prompt in zip(frame_items, descriptions, final_prompts):
        results.append({
            "frame_path": item["frame_path"],
            "description": desc,
            "prompt": prompt,
            "raw": f"## 画面描述词\n{desc}\n\n## AI提示词\n{prompt}",
        })
    return results
