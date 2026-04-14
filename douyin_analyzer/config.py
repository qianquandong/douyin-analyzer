import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_OUTPUT_DIR = "./output"
WHISPER_MODEL = "medium"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_IMAGE_SIZE_BYTES = 4 * 1024 * 1024  # 4MB

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── 第一步：生成视频画面描述词（用于图片生成还原） ──
STAGE1_PROMPT = """根据这张视频关键帧画面（镜头时长：{duration}秒），帮我生成对应的视频画面描述词，用于图片生成还原。

请从以下几个方面拆解这个镜头：
- 核心画面(Subject)：画面里的主体是什么？（人物、物体、风景）
- 环境背景(Environment)：发生在什么地方？（室内室外、光影、天气）
- 艺术风格(Art Style)：画面风格是什么？（例如：电影感、赛博朋克、水彩、吉卜力风格、超写实摄影等）
- 构图与镜头(Composition & Camera)：镜头视角（特写、广角、俯视）、景深等
- 细节修饰(Details & Lighting)：灯光、材质、色彩氛围

要求：
1. 用中文纯文字描述，不要用表格
2. 不需要字幕
3. 描述要能让即梦等AI工具还原出与原视频1:1的画面
4. 一段自然流畅的中文描述即可，不要分点，不要标题"""

# ── 第二步：基于统一风格模板生成最终 AI 提示词 ──
STAGE2_PROMPT = """你是一个专业的视觉导演。以下是一段视频的分镜描述（共 {n} 个镜头），请为每个镜头生成高质量的中文 AI 提示词，保证整体风格统一。

【统一风格模板】：
{style}

要求：
1. 所有镜头必须统一上述风格
2. 风格要自然融入画面，不允许简单拼接
3. 每条提示词必须包含：主体、场景、镜头语言、光影、色彩、情绪、画面拍摄设备/设备参数
4. 保证整体风格统一，同时根据镜头内容进行合理变化
5. 用中文输出
6. 每条提示词 80-150 字，紧凑自然

【分镜列表】：
{shot_list}

请严格按以下格式输出，每个镜头一段：

## 镜头1
<该镜头的中文 AI 提示词>

## 镜头2
<该镜头的中文 AI 提示词>

（以此类推，共 {n} 条）"""

# 默认风格模板（用户可通过 --style-template 参数覆盖）
DEFAULT_STYLE_TEMPLATE = (
    "电影感纪实摄影风格，温暖自然光，浅景深，富士胶片色调，"
    "日系美食杂志质感，画面细腻真实，情绪沉静舒缓"
)

DOUYIN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.douyin.com/",
}
