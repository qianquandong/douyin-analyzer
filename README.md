# 抖音视频分析工具

下载抖音视频，自动检测关键帧、转录语音文案、用 AI 生成图片提示词。

## 功能

- **视频下载** — 支持抖音各种链接格式（短链接、完整链接、modal_id）
- **关键帧检测** — PySceneDetect 自动检测场景切换，>3秒场景截首帧+尾帧
- **语音转文字** — OpenAI Whisper 本地转录中文语音
- **AI 提示词生成** — Claude API 分析每帧画面，生成通用英文图片提示词（适配 Midjourney / Stable Diffusion / DALL-E）
- **双格式报告** — 同时输出 Markdown 报告和 Excel 表格

## 安装

```bash
# 系统依赖
brew install ffmpeg  # macOS

# Python 依赖（需要 Python 3.10+）
python3 -m venv .venv
source .venv/bin/activate
pip install setuptools
pip install llvmlite==0.43.0 numba==0.60.0
pip install --no-build-isolation openai-whisper==20240930
pip install -r requirements.txt
```

## 配置

```bash
export ANTHROPIC_API_KEY=your_api_key_here
# 或创建 .env 文件
cp .env.example .env
```

## 使用

```bash
source .venv/bin/activate

# 完整分析
python -m douyin_analyzer "https://www.douyin.com/video/xxxxx"

# 跳过语音转录
python -m douyin_analyzer "URL" --skip-transcription

# 跳过 AI 分析（不需要 API Key）
python -m douyin_analyzer "URL" --skip-analysis

# 自定义参数
python -m douyin_analyzer "URL" \
  --whisper-model small \
  --scene-threshold 20 \
  --cookies-from firefox \
  --output ./my_output
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--output, -o` | `./output` | 输出目录 |
| `--whisper-model` | `medium` | Whisper 模型 (tiny/base/small/medium/large-v3) |
| `--scene-threshold` | `27.0` | 场景检测灵敏度，越低检测越多场景 |
| `--cookies-from` | `chrome` | 从哪个浏览器读取抖音 cookies |
| `--skip-transcription` | - | 跳过语音转文字 |
| `--skip-analysis` | - | 跳过 AI 图片分析 |

## 输出结构

```
output/<video_id>/
├── video.mp4          # 原视频
├── audio.wav          # 提取的音频
├── frames/            # 关键帧截图
│   ├── scene_001.jpg
│   ├── scene_003_a.jpg  # 首帧（场景>3秒）
│   ├── scene_003_b.jpg  # 尾帧
│   └── ...
├── report.md          # Markdown 分析报告
└── report.xlsx        # Excel 分析报告
```

## 技术栈

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — 视频下载
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) — 场景检测
- [OpenAI Whisper](https://github.com/openai/whisper) — 语音识别
- [Claude API](https://docs.anthropic.com/) — 图片分析与提示词生成
- [Click](https://click.palletsprojects.com/) + [Rich](https://rich.readthedocs.io/) — CLI 界面
