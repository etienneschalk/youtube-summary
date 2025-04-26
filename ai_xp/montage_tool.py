import json
import os
import shutil
import subprocess
from typing import Optional

import click
from moviepy import VideoFileClip, concatenate_videoclips

try:
    from pytube import YouTube

    PYTUBE_AVAILABLE = True
except ImportError:
    PYTUBE_AVAILABLE = False


DEFAULT_DOWNLOADED_VIDEOS_OUTPUT_DIR = "generated/downloaded_videos"
DEFAULT_TEMP_CLIPS_OUTPUT_DIR = "generated/temp_clips"
DEFAULT_CLIPPED_VIDEOS_OUTPUT_DIR = "generated/clips/montage.mp4"


def download_youtube_video_pytube(
    url: str, output_path: str = DEFAULT_DOWNLOADED_VIDEOS_OUTPUT_DIR
) -> Optional[str]:
    """Download a YouTube video.

    Parameters
    ----------
    url : str
        URL of the YouTube video.
    output_path : str, optional
        Directory where the video will be saved (default is 'downloads').

    Returns
    -------
    Optional[str]
        Path to the downloaded video file, or None if download fails.
    """
    try:
        yt = YouTube(url)
        stream = (
            yt.streams.filter(progressive=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
            .first()
        )
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        video_path = stream.download(output_path=output_path)
        print(f"Video downloaded to {video_path}")
        return video_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None


def download_youtube_video_youtubedl(
    url: str, output_path: str = DEFAULT_DOWNLOADED_VIDEOS_OUTPUT_DIR
) -> Optional[str]:
    """Download a YouTube video using youtube-dl."""
    return _download_with_tool(url, output_path, tool="youtube-dl")


def download_youtube_video_ytdlp(
    url: str, output_path: str = DEFAULT_DOWNLOADED_VIDEOS_OUTPUT_DIR
) -> Optional[str]:
    """Download a YouTube video using yt-dlp."""
    return _download_with_tool(url, output_path, tool="yt-dlp")


def _download_with_tool(url: str, output_path: str, tool: str) -> Optional[str]:
    """Helper function to download with youtube-dl or yt-dlp."""
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output_template = os.path.join(output_path, "%(title)s.%(ext)s")
        cmd = [tool, "-f", "best[ext=mp4]", "-o", output_template, url]
        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        files = sorted(
            os.listdir(output_path),
            key=lambda x: os.path.getctime(os.path.join(output_path, x)),
        )
        if files:
            downloaded_file = os.path.join(output_path, files[-1])
            print(f"Video downloaded to {downloaded_file}")
            return downloaded_file
        else:
            print("No file found after download.")
            return None
    except Exception as e:
        print(f"Error downloading video with {tool}: {e}")
        return None


def auto_select_downloader() -> str:
    """Auto-detect available video downloader."""
    if shutil.which("yt-dlp"):
        return "yt-dlp"
    elif shutil.which("youtube-dl"):
        return "youtube-dl"
    elif PYTUBE_AVAILABLE:
        return "pytube"
    else:
        raise RuntimeError(
            "No downloader available (need pytube, yt-dlp or youtube-dl)"
        )


# def download_youtube_video_youtubedl(
#     url: str, output_path: str = DEFAULT_DOWNLOADED_VIDEOS_OUTPUT_DIR
# ) -> Optional[str]:
#     """Download a YouTube video using youtube-dl.

#     Parameters
#     ----------
#     url : str
#         URL of the YouTube video.
#     output_path : str, optional
#         Directory where the video will be saved (default is 'downloads').

#     Returns
#     -------
#     Optional[str]
#         Path to the downloaded video file, or None if download fails.
#     """
#     try:
#         if not os.path.exists(output_path):
#             os.makedirs(output_path)
#         output_template = os.path.join(output_path, "%(title)s.%(ext)s")
#         cmd = ["youtube-dl", "-f", "best[ext=mp4]", "-o", output_template, url]
#         subprocess.run(cmd, check=True)

#         # Find the latest downloaded file
#         files = sorted(
#             os.listdir(output_path),
#             key=lambda x: os.path.getctime(os.path.join(output_path, x)),
#         )
#         if files:
#             downloaded_file = os.path.join(output_path, files[-1])
#             print(f"Video downloaded to {downloaded_file}")
#             return downloaded_file
#         else:
#             print("No file found after download.")
#             return None
#     except Exception as e:
#         print(f"Error downloading video with youtube-dl: {e}")
#         return None


def extract_clips_moviepy(
    video_path: str,
    clip_duration: int = 5,
    interval: int = 60,
    segments: Optional[list[dict[str, float]]] = None,
) -> list[VideoFileClip]:
    """Extract clips from a video using MoviePy.

    Parameters
    ----------
    video_path : str
        Path to the source video.
    clip_duration : int, optional
        Duration of each extracted clip in seconds (default is 5).
    interval : int, optional
        Time interval between the start of each clip in seconds (default is 60).
    segments : Optional[list[dict[str, float]]], optional
        list of specific segments to extract, each with 'start' and 'duration'.

    Returns
    -------
    list[VideoFileClip]
        list of extracted video clips.
    """
    clips = []
    try:
        video = VideoFileClip(video_path)
        # XXX video is not closed ; if it is closed, then clips point to nothing.
        # Better resource mgmgt is needed.
        if segments:
            for seg in segments:
                start = seg["start"]
                duration = seg["duration"]
                clip = video.subclipped(start, start + duration)
                clips.append(clip)
        else:
            total_duration = int(video.duration)
            for start_time in range(0, total_duration, interval):
                if start_time + clip_duration <= total_duration:
                    clip = video.subclipped(start_time, start_time + clip_duration)
                    clips.append(clip)
        return clips
        # with VideoFileClip(video_path) as video:
        #     if segments:
        #         for seg in segments:
        #             start = seg["start"]
        #             duration = seg["duration"]
        #             clip = video.subclipped(start, start + duration)
        #             clips.append(clip)
        #     else:
        #         total_duration = int(video.duration)
        #         for start_time in range(0, total_duration, interval):
        #             if start_time + clip_duration <= total_duration:
        #                 clip = video.subclipped(start_time, start_time + clip_duration)
        #                 clips.append(clip)
        #     return clips
    except Exception as e:
        print(f"Error extracting clips with moviepy: {e}")
        return []


def extract_clips_ffmpeg(
    video_path: str,
    output_dir: str = DEFAULT_TEMP_CLIPS_OUTPUT_DIR,
    clip_duration: int = 5,
    interval: int = 60,
    segments: Optional[list[dict[str, float]]] = None,
) -> list[str]:
    """Extract clips from a video using ffmpeg.

    Parameters
    ----------
    video_path : str
        Path to the source video.
    output_dir : str, optional
        Directory where clips will be saved (default is 'temp_clips').
    clip_duration : int, optional
        Duration of each extracted clip in seconds (default is 5).
    interval : int, optional
        Time interval between the start of each clip in seconds (default is 60).
    segments : Optional[list[dict[str, float]]], optional
        list of specific segments to extract, each with 'start' and 'duration'.

    Returns
    -------
    list[str]
        list of paths to extracted clip files.
    """
    clips = []
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        video = VideoFileClip(video_path)
        if segments:
            for idx, seg in enumerate(segments):
                start = seg["start"]
                duration = seg["duration"]
                output_clip = os.path.join(output_dir, f"clip_{idx}.mp4")
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    video_path,
                    "-ss",
                    str(start),
                    "-t",
                    str(duration),
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    output_clip,
                ]
                subprocess.run(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                clips.append(output_clip)
        else:
            total_duration = int(video.duration)
            for idx, start_time in enumerate(range(0, total_duration, interval)):
                if start_time + clip_duration <= total_duration:
                    output_clip = os.path.join(output_dir, f"clip_{idx}.mp4")
                    cmd = [
                        "ffmpeg",
                        "-y",
                        "-i",
                        video_path,
                        "-ss",
                        str(start_time),
                        "-t",
                        str(clip_duration),
                        "-c:v",
                        "libx264",
                        "-c:a",
                        "aac",
                        output_clip,
                    ]
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    clips.append(output_clip)
        return clips
    except Exception as e:
        print(f"Error extracting clips with ffmpeg: {e}")
        return []


def create_montage_moviepy(
    clips: list[VideoFileClip], output_path: str = DEFAULT_CLIPPED_VIDEOS_OUTPUT_DIR
) -> None:
    """Create a montage from clips using MoviePy.

    Parameters
    ----------
    clips : list[VideoFileClip]
        list of video clips.
    output_path : str, optional
        Path to save the final montage video (default is 'montage.mp4').

    Returns
    -------
    None
    """
    try:
        if clips:
            final_clip = concatenate_videoclips(clips)
            final_clip.write_videofile(output_path, codec="libx264")
            print(f"Montage created at {output_path}")
        else:
            print("No clips to montage!")
    except Exception as e:
        print(f"Error creating montage with moviepy: {e}")


def create_montage_ffmpeg(
    clips_paths: list[str], output_path: str = DEFAULT_CLIPPED_VIDEOS_OUTPUT_DIR
) -> None:
    """Create a montage from clip files using ffmpeg.

    Parameters
    ----------
    clips_paths : list[str]
        list of paths to video clips.
    output_path : str, optional
        Path to save the final montage video (default is 'montage.mp4').

    Returns
    -------
    None
    """
    try:
        list_file = "clips_list.txt"
        with open(list_file, "w") as f:
            for clip_path in clips_paths:
                f.write(f"file '{os.path.abspath(clip_path)}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_file,
            "-c",
            "copy",
            output_path,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"Montage created at {output_path}")

        os.remove(list_file)
    except Exception as e:
        print(f"Error creating montage with ffmpeg: {e}")


def clean_up(paths: list[str]) -> None:
    """Delete files or directories.

    Parameters
    ----------
    paths : list[str]
        list of paths to delete.

    Returns
    -------
    None
    """
    return  # TODO eschalk actually clean up
    for path in paths:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)


@click.command()
@click.argument("youtube_url")
@click.option(
    "--method",
    type=click.Choice(["moviepy", "ffmpeg"]),
    default="moviepy",
    help="Extraction method",
)
@click.option(
    "--downloader",
    type=click.Choice(["auto", "pytube", "youtube-dl", "yt-dlp"]),
    default="auto",
    help="Downloader to use",
)
@click.option(
    "--segments-file",
    type=click.Path(exists=True),
    default=None,
    help="JSON file with segments",
)
@click.option("--clip-duration", default=5, help="Duration of each clip (in seconds)")
@click.option("--interval", default=60, help="Interval between clips (in seconds)")
@click.option(
    "--output",
    default=DEFAULT_CLIPPED_VIDEOS_OUTPUT_DIR,
    help="Output montage file path",
)
def main(
    youtube_url: str,
    method: str,
    downloader: str,
    segments_file: Optional[str],
    clip_duration: int,
    interval: int,
    output: str,
) -> None:
    """Main function to orchestrate downloading, extracting clips, and creating a montage.

    Parameters
    ----------
    youtube_url : str
        URL of the YouTube video.
    method : str
        Extraction method: 'moviepy' or 'ffmpeg'.
    downloader : str
        Downloader tool to use: 'pytube', 'youtube-dl', 'yt-dlp', or 'auto' (default).
    segments_file : Optional[str]
        Path to JSON file specifying custom segments.
    clip_duration : int
        Duration of each clip in seconds.
    interval : int
        Interval between clips in seconds.
    output : str
        Output path for the final montage video.

    Returns
    -------
    None
    """
    segments = None
    if segments_file:
        try:
            with open(segments_file, "r") as f:
                segments = json.load(f)
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier de segments : {e}")

    # Select downloader
    if downloader == "auto":
        downloader = auto_select_downloader()

    if downloader == "pytube":
        downloaded_video = download_youtube_video_pytube(youtube_url)
    elif downloader == "youtube-dl":
        downloaded_video = download_youtube_video_youtubedl(youtube_url)
    elif downloader == "yt-dlp":
        downloaded_video = download_youtube_video_ytdlp(youtube_url)
    else:
        print("Invalid downloader specified.")
        return

    if not downloaded_video:
        print("Download failed.")
        return

    # return  # TODO eschalk do not attempt montage

    # Process video
    if method == "moviepy":
        clips = extract_clips_moviepy(
            downloaded_video, clip_duration, interval, segments
        )
        create_montage_moviepy(clips, output)
    elif method == "ffmpeg":
        # XXX TODO eschalk untested
        clips = extract_clips_ffmpeg(
            downloaded_video,
            DEFAULT_TEMP_CLIPS_OUTPUT_DIR,
            clip_duration,
            interval,
            segments,
        )
        create_montage_ffmpeg(clips, output)
        clean_up([DEFAULT_CLIPPED_VIDEOS_OUTPUT_DIR])
    else:
        print("Methode non reconnue. Veuillez choisir 'moviepy' ou 'ffmpeg'.")

    clean_up([downloaded_video])


# Tes fonctions extract_clips_moviepy, extract_clips_ffmpeg, create_montage_moviepy, create_montage_ffmpeg, clean_up restent inchangées

if __name__ == "__main__":
    main()
