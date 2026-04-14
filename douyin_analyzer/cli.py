import os
import sys

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import (
    ANTHROPIC_API_KEY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_STYLE_TEMPLATE,
    WHISPER_MODEL,
)
from .downloader import download_video
from .image_analyzer import analyze_all_frames, create_client
from .report import generate_excel, generate_report
from .scene_detect import detect_scenes
from .transcriber import extract_audio, transcribe_audio
from .utils import ensure_ffmpeg, extract_video_id

console = Console()


@click.command()
@click.argument("url")
@click.option("--output", "-o", default=DEFAULT_OUTPUT_DIR, help="输出目录")
@click.option(
    "--whisper-model",
    default=WHISPER_MODEL,
    type=click.Choice(["tiny", "base", "small", "medium", "large-v3"]),
    help="Whisper模型大小",
)
@click.option(
    "--scene-threshold",
    default=27.0,
    help="场景检测灵敏度（越低检测到越多场景）",
)
@click.option("--skip-transcription", is_flag=True, help="跳过语音转文字")
@click.option("--skip-analysis", is_flag=True, help="跳过AI图片分析")
@click.option(
    "--cookies-from",
    default="chrome",
    type=click.Choice(["chrome", "firefox", "edge", "safari"]),
    help="从哪个浏览器读取抖音cookies",
)
@click.option(
    "--style-template",
    default=DEFAULT_STYLE_TEMPLATE,
    help="第二步生成最终AI提示词时的统一风格模板（中文）",
)
def analyze(url, output, whisper_model, scene_threshold, skip_transcription, skip_analysis, cookies_from, style_template):
    """分析抖音视频：下载 → 关键帧检测 → 语音转文字 → AI提示词生成

    URL: 抖音视频链接（支持短链接和完整链接）
    """
    # 前置检查
    ensure_ffmpeg()
    if not skip_analysis and not ANTHROPIC_API_KEY:
        console.print(
            "[red]错误: 未设置 ANTHROPIC_API_KEY[/red]\n"
            "请设置环境变量或在 .env 文件中配置",
        )
        sys.exit(1)

    video_id = extract_video_id(url)
    output_dir = os.path.join(output, video_id)
    frames_dir = os.path.join(output_dir, "frames")
    audio_path = os.path.join(output_dir, "audio.wav")

    console.print(f"\n[bold]抖音视频分析工具[/bold]")
    console.print(f"输出目录: {output_dir}\n")

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )

    with progress:
        # Step 1: 下载视频
        task = progress.add_task("正在下载视频...", total=None)
        video_info = download_video(url, output_dir, cookies_from=cookies_from)
        progress.update(task, description="[green]视频下载完成[/green]")
        progress.remove_task(task)
        console.print(f"  标题: {video_info['title']}")
        console.print(f"  时长: {video_info['duration']}秒\n")

        # Step 2: 检测关键帧
        task = progress.add_task("正在检测关键帧...", total=None)
        scenes = detect_scenes(
            video_info["video_path"], frames_dir, threshold=scene_threshold
        )
        total_frames = sum(len(s["frame_paths"]) for s in scenes)
        progress.update(task, description=f"[green]检测到 {len(scenes)} 个场景，共 {total_frames} 张关键帧[/green]")
        progress.remove_task(task)
        console.print()

        # Step 3: 语音转文字
        transcription = None
        if not skip_transcription:
            task = progress.add_task("正在提取音频...", total=None)
            extract_audio(video_info["video_path"], audio_path)
            progress.update(task, description="正在转录语音（可能需要几分钟）...")
            transcription = transcribe_audio(audio_path, whisper_model)
            progress.update(task, description="[green]语音转录完成[/green]")
            progress.remove_task(task)
            if transcription["text"]:
                console.print(f"  转录文本: {transcription['text'][:100]}...\n")
            else:
                console.print("  未检测到语音内容\n")

        # Step 4: AI分析关键帧（两步流程）
        analyses = None
        if not skip_analysis:
            client = create_client(ANTHROPIC_API_KEY)
            # 准备 frame + duration 列表
            frame_items = []
            for s in scenes:
                dur = s["end"] - s["start"]
                for fp in s["frame_paths"]:
                    frame_items.append({"frame_path": fp, "duration": dur})
            n_total = len(frame_items)

            task = progress.add_task(
                f"第一步：生成画面描述词 0/{n_total}...", total=None
            )

            def _cb(i, n, stage):
                if stage == "stage1":
                    progress.update(
                        task, description=f"第一步：生成画面描述词 {i}/{n}..."
                    )
                elif stage == "stage2":
                    progress.update(
                        task,
                        description="第二步：统一风格生成最终AI提示词...",
                    )

            analyses = analyze_all_frames(
                client, frame_items, style_template, progress_callback=_cb
            )
            progress.update(task, description="[green]AI分析完成[/green]")
            progress.remove_task(task)
            console.print(f"  风格模板: {style_template[:50]}...\n")

        # Step 5: 生成报告
        task = progress.add_task("正在生成报告...", total=None)
        report_path = generate_report(
            video_info, url, scenes, transcription, analyses, output_dir
        )
        xlsx_path = generate_excel(
            video_info, url, scenes, transcription, analyses, output_dir
        )
        progress.update(task, description="[green]报告生成完成[/green]")
        progress.remove_task(task)

    console.print(f"\n[bold green]分析完成！[/bold green]")
    console.print(f"Markdown报告: {report_path}")
    console.print(f"Excel报告:    {xlsx_path}")
    console.print(f"关键帧目录:   {frames_dir}")


def main():
    analyze()


if __name__ == "__main__":
    main()
