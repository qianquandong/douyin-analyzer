import os

import cv2
from scenedetect import open_video, SceneManager, ContentDetector


def detect_scenes(
    video_path: str, frames_dir: str, threshold: float = 27.0
) -> list[dict]:
    """
    检测视频场景切换并保存关键帧。

    返回:
        list[dict]: [{"scene_num": 1, "start": 0.0, "end": 3.5,
                       "frame_path": "frames/scene_001.jpg"}, ...]
    """
    os.makedirs(frames_dir, exist_ok=True)

    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    # 如果场景太少，按时间间隔采样
    if len(scene_list) < 2:
        return _sample_frames(video_path, frames_dir, interval=3.0)

    results = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    for i, (start, end) in enumerate(scene_list, 1):
        start_sec = start.get_seconds()
        end_sec = end.get_seconds()
        duration = end_sec - start_sec
        frame_paths = []

        if duration > 3.0:
            # 大于3秒：截首帧和尾帧
            for tag, sec in [("a", start_sec + 0.1), ("b", end_sec - 0.1)]:
                idx = int(sec * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    fname = f"scene_{i:03d}_{tag}.jpg"
                    path = os.path.join(frames_dir, fname)
                    cv2.imwrite(path, frame)
                    frame_paths.append(path)
        else:
            # 3秒以内：截中间帧
            mid_sec = (start_sec + end_sec) / 2
            idx = int(mid_sec * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                fname = f"scene_{i:03d}.jpg"
                path = os.path.join(frames_dir, fname)
                cv2.imwrite(path, frame)
                frame_paths.append(path)

        if frame_paths:
            results.append({
                "scene_num": i,
                "start": start_sec,
                "end": end_sec,
                "frame_paths": frame_paths,
            })

    cap.release()
    return results


def _sample_frames(
    video_path: str, frames_dir: str, interval: float = 3.0
) -> list[dict]:
    """当场景检测结果过少时，按固定时间间隔采样帧。"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    results = []
    current = 0.0
    scene_num = 1

    while current < duration:
        frame_idx = int(current * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        end_sec = min(current + interval, duration)
        frame_filename = f"scene_{scene_num:03d}.jpg"
        frame_path = os.path.join(frames_dir, frame_filename)
        cv2.imwrite(frame_path, frame)

        results.append({
            "scene_num": scene_num,
            "start": current,
            "end": end_sec,
            "frame_paths": [frame_path],
        })

        current += interval
        scene_num += 1

    cap.release()
    return results
