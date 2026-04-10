import base64
from pathlib import Path

import anthropic

from .config import ANALYSIS_PROMPT, CLAUDE_MODEL
from .utils import resize_image_if_needed


def create_client(api_key: str) -> anthropic.Anthropic:
    """创建Anthropic API客户端。"""
    return anthropic.Anthropic(api_key=api_key)


def analyze_frame(client: anthropic.Anthropic, image_path: str) -> dict:
    """
    使用Claude分析单张关键帧图片。

    返回:
        dict: {"description": "中文描述", "prompt": "英文提示词", "raw": "完整响应"}
    """
    # 确保图片大小在限制内
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

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": ANALYSIS_PROMPT,
                    },
                ],
            }
        ],
    )

    raw_text = message.content[0].text
    return _parse_analysis(raw_text)


def _parse_analysis(text: str) -> dict:
    """解析Claude返回的分析结果。"""
    description = ""
    prompt = ""

    sections = text.split("## ")
    for section in sections:
        if section.startswith("画面描述"):
            description = section.replace("画面描述", "").strip().strip("\n")
        elif section.startswith("通用提示词"):
            prompt = section.replace("通用提示词", "").strip().strip("\n")

    return {
        "description": description or text,
        "prompt": prompt or text,
        "raw": text,
    }


def analyze_frames(
    client: anthropic.Anthropic, frame_paths: list[str]
) -> list[dict]:
    """批量分析多张关键帧。"""
    results = []
    for path in frame_paths:
        result = analyze_frame(client, path)
        result["frame_path"] = path
        results.append(result)
    return results
