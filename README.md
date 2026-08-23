# Douyin Analyzer

**English** | [中文](./README.zh-CN.md)

Take any Douyin video apart: download it, detect keyframes, transcribe the narration with Whisper, and reverse-engineer an image prompt for every shot.

## Features

- **Video download** — handles every Douyin link format (short links, full links, modal_id)
- **Keyframe detection** — PySceneDetect finds scene cuts automatically; scenes longer than 3 seconds get both a first and a last frame
- **Speech to text** — local Chinese transcription with OpenAI Whisper
- **AI prompt generation** — Claude API analyzes each frame and writes a portable English image prompt (works with Midjourney / Stable Diffusion / DALL-E)
- **Two report formats** — a Markdown report and an Excel sheet, generated together

## Install

```bash
# System dependency
brew install ffmpeg  # macOS

# Python dependencies (Python 3.10+)
python3 -m venv .venv
source .venv/bin/activate
pip install setuptools
pip install llvmlite==0.43.0 numba==0.60.0
pip install --no-build-isolation openai-whisper==20240930
pip install -r requirements.txt
```

## Configure

```bash
export ANTHROPIC_API_KEY=your_api_key_here
# or create a .env file
cp .env.example .env
```

## Use

```bash
source .venv/bin/activate

# Full analysis
python -m douyin_analyzer "https://www.douyin.com/video/xxxxx"

# Skip transcription
python -m douyin_analyzer "URL" --skip-transcription

# Skip AI analysis (no API key needed)
python -m douyin_analyzer "URL" --skip-analysis

# Custom parameters
python -m douyin_analyzer "URL" \
  --whisper-model small \
  --scene-threshold 20 \
  --cookies-from firefox \
  --output ./my_output
```

## Parameters

| Flag | Default | What it does |
|------|---------|--------------|
| `--output, -o` | `./output` | Output directory |
| `--whisper-model` | `medium` | Whisper model (tiny/base/small/medium/large-v3) |
| `--scene-threshold` | `27.0` | Scene-detection sensitivity; lower detects more scenes |
| `--cookies-from` | `chrome` | Which browser to read Douyin cookies from |
| `--skip-transcription` | — | Skip speech-to-text |
| `--skip-analysis` | — | Skip AI frame analysis |

## Output layout

```
output/<video_id>/
├── video.mp4          # original video
├── audio.wav          # extracted audio
├── frames/            # keyframe captures
│   ├── scene_001.jpg
│   ├── scene_003_a.jpg  # first frame (scene > 3s)
│   ├── scene_003_b.jpg  # last frame
│   └── ...
├── report.md          # Markdown report
└── report.xlsx        # Excel report
```

## Built with

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — video download
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) — scene detection
- [OpenAI Whisper](https://github.com/openai/whisper) — speech recognition
- [Claude API](https://docs.anthropic.com/) — frame analysis and prompt generation
- [Click](https://click.palletsprojects.com/) + [Rich](https://rich.readthedocs.io/) — CLI
