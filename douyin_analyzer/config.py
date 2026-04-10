import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_OUTPUT_DIR = "./output"
WHISPER_MODEL = "medium"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_IMAGE_SIZE_BYTES = 4 * 1024 * 1024  # 4MB

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

ANALYSIS_PROMPT = """请详细分析这张图片，然后生成一段通用的图像生成提示词（prompt），要求：
1. 用英文撰写提示词
2. 描述画面的主体、构图、光线、色调、风格、氛围
3. 提示词应适配多个AI图像生成平台（如Midjourney、Stable Diffusion、DALL-E等）
4. 不要包含任何平台特定的参数或语法（如 --ar, --v, <lora> 等）
5. 提示词长度控制在50-150个英文单词

请先用中文简要描述画面内容，然后给出英文提示词。

输出格式：
## 画面描述
（中文描述）

## 通用提示词
（英文prompt）"""

DOUYIN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.douyin.com/",
}
