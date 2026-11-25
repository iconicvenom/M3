"""Build the silent master, its companion documents, or the student's narrated export."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
BUILD = ROOT / ".build" / "production"
MASTER = OUT / "Vectors_Silent.mp4"
FPS = 30


def run(*args, capture=False, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, capture_output=capture, text=True, **kwargs)


def inspect(path):
    return json.loads(run("ffprobe", "-v", "error", "-show_streams", "-show_format",
                          "-of", "json", path, capture=True).stdout)


def media_check(path, size, fps, frames, voiced=False):
    info = inspect(path)
    streams = info["streams"]
    kinds = [s["codec_type"] for s in streams]
    if kinds != (["video", "audio"] if voiced else ["video"]):
        raise ValueError(f"Unexpected streams in {path}: {kinds}")
    v = streams[0]
    actual = (v["width"], v["height"], v["pix_fmt"], v["codec_name"],
              v["avg_frame_rate"], int(v["nb_frames"]))
    expected = (*size, "yuv420p", "h264", f"{fps}/1", frames)
    if actual != expected or abs(float(v["duration"]) - frames / fps) > .001:
        raise ValueError(f"Video differs from timeline or export spec: {actual}; expected {expected}")
    duration = float(info["format"]["duration"])
    if duration >= 420:
        raise ValueError(f"{duration:.3f}s reaches the strict seven-minute limit.")
    if voiced:
        a = streams[1]
        if a["codec_name"] != "aac" or abs(float(a["duration"]) - frames / fps) > .030:
            raise ValueError("AAC stream does not cover the intended timeline.")
        log = run("ffmpeg", "-nostats", "-i", path, "-map", "0:a:0", "-af", "ebur128",
                  "-f", "null", "-", capture=True).stderr
        loudness = float(re.findall(r"I:\s+([-\d.]+) LUFS", log)[-1])
        if loudness < -50:
            raise ValueError(f"Very quiet or silent recording ({loudness:.1f} LUFS). Check microphone level.")
        print(f"Encoded audio loudness: {loudness:.1f} LUFS")
    run("ffmpeg", "-xerror", "-v", "error", "-i", path, "-map", "0", "-f", "null", "-")
    print(f"Verified {frames} frames at {fps} fps, {duration:.3f}s, {kinds}; full decode passed.")


def render(temp, preview=None):
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([str(ROOT/".venv/bin"), str(ROOT/".texlive/bin/universal-darwin"), str(ROOT.parent/".texlive/bin/universal-darwin"),
                                   env["PATH"]])
    env["VECTORS_CLIP"] = preview or "master"
    size, fps, seconds = ((960,540),30,24) if preview else ((1920,1080),FPS,300)
    result = temp / "render.mp4"
    run(Path(sys.executable).parent/"manim", "render", "--disable_caching", "--progress_bar", "none",
        "--renderer", "cairo", "-r", f"{size[0]},{size[1]}", "--fps", fps, "-o", result,
        ROOT/"Code/vectors.py", "Vectors", env=env, cwd=ROOT)
    media_check(result,size,fps,seconds*fps)
    target = OUT/f"Vectors_{preview.title()}Preview.mp4" if preview else MASTER
    result.replace(target)
    print(target)


def add_voice(path, temp):
    if not path or not path.is_file():
        raise ValueError("Supply your recorded WAV, M4A or MP3 as a quoted path.")
    source = next((s for s in inspect(path)["streams"] if s["codec_type"]=="audio"), None)
    if source is None:
        raise ValueError("The supplied file has no audio stream.")
    print(f'Input audio: {source["codec_name"]}, reported duration {source.get("duration","unknown")}s.')
    video_seconds = 300
    media_check(MASTER,(1920,1080),FPS,video_seconds*FPS)
    # Decode the selected stream fully. Count PCM samples after handling codec delay.
    pcm = temp / "recording.wav"
    run("ffmpeg","-v","error","-i",path,"-map","0:a:0","-ar",48000,"-ac",1,"-c:a","pcm_s16le",pcm)
    pcm_stream = inspect(pcm)["streams"][0]
    samples = int(pcm_stream["duration_ts"])
    seconds = samples / 48000
    frames = max(video_seconds * FPS, math.ceil(samples * FPS / 48000))
    if abs(seconds-video_seconds)>2:
        raise ValueError(f"Recording {seconds:.3f}s versus picture {video_seconds}s. Align the take to the timed script and retry. No output replaced.")
    if abs(seconds - video_seconds) > 1/FPS:
        print(f"Timing mismatch: recording {seconds:.3f}s, picture {video_seconds}s. "
              "A shorter take leaves a quiet ending; a longer take extends the credits. "
              "Review the take against the recording script.")
    else:
        print(f"Measured recording: {seconds:.3f}s. Picture matches within one frame.")
    if frames / FPS >= 420:
        raise ValueError("Keeping the entire take would reach seven minutes. Supply a shorter take.")
    extra = frames - video_seconds*FPS
    video_args = ["-c:v","copy"] if extra == 0 else [
        "-vf",f"tpad=stop_mode=clone:stop={extra}","-c:v","libx264","-crf","18","-pix_fmt","yuv420p"]
    final = temp / "final.mp4"
    run("ffmpeg","-v","error","-i",MASTER,"-i",pcm,"-map","0:v:0","-map","1:a:0",
        *video_args,"-af",f"apad=whole_len={frames*48000//FPS}","-c:a","aac","-b:a","160k",
        "-movflags","+faststart",final)
    media_check(final,(1920,1080),FPS,frames,voiced=True)
    final.replace(OUT/"Vectors_Final.mp4")
    print(OUT/"Vectors_Final.mp4")


def clock(seconds):
    value = round(seconds)
    return f"{value//60}:{value%60:02}"


def documents(temp):
    from storyboard import save_board

    scenes = json.loads((ROOT/"Code/board.json").read_text())
    media_check(MASTER, (1920,1080), FPS, 300*FPS)
    for i, scene in enumerate(scenes):
        still = temp / f"scene-{i}.png"
        run("ffmpeg", "-v", "error", "-ss", scene["still_time"], "-i", MASTER,
            "-frames:v", "1", "-vf", "scale=1280:720", still)
        scene["image"] = str(still)
    save_board(scenes, temp/"board.pdf", clock)
    (temp/"board.pdf").replace(ROOT/"Storyboard.pdf")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["preview","master","documents","rebuild","voice"])
    parser.add_argument("recording",nargs="?",type=Path)
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    BUILD.mkdir(parents=True,exist_ok=True)
    with (ROOT/".build/render.lock").open("a") as lock, tempfile.TemporaryDirectory(dir=BUILD) as tmp:
        fcntl.flock(lock,fcntl.LOCK_EX)
        temp=Path(tmp)
        if args.command in ("master","rebuild","preview"):
            render(temp,preview={"preview":"motion"}.get(args.command))
        if args.command in ("rebuild","documents"):
            documents(temp)
        if args.command=="voice":
            add_voice(args.recording,temp)


if __name__=="__main__":
    main()
