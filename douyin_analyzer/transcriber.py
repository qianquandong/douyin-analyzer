import subprocess

import whisper

from .utils import ensure_ffmpeg


def extract_audio(video_path: str, audio_path: str) -> str:
    """从视频中提取音频为WAV格式。"""
    ensure_ffmpeg()
    subprocess.run(
        [
            "ffmpeg", "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            audio_path,
        ],
        check=True,
        capture_output=True,
    )
    return audio_path


def transcribe_audio(audio_path: str, model_name: str = "medium") -> dict:
    """
    使用Whisper转录音频为中文文本。

    返回:
        dict: {"text": "完整文本", "segments": [{"start": 0.0, "end": 2.5, "text": "..."}, ...]}
    """
    model = whisper.load_model(model_name)
    result = model.transcribe(
        audio_path,
        language="zh",
        task="transcribe",
        verbose=False,
    )
    return {
        "text": result.get("text", ""),
        "segments": [
            {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
            }
            for seg in result.get("segments", [])
        ],
    }
