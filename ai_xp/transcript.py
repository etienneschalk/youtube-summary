import requests
import json
from dataclasses import dataclass, field

from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs


def get_youtube_transcript(
    video_url: str,
    languages: tuple[str, ...] | str,
) -> str | None:
    # ISO 639-1 language code
    languages = (languages,) if isinstance(languages, str) else languages
    video_id = extract_video_id(video_url)
    try:
        # Try preferred language. If the language is not available this will fail.
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)  # type: ignore
        # An entry contains text, start and duration.
        full_text = " ".join([entry["text"] for entry in transcript])  # type: ignore
        return full_text
    except Exception as exc:
        print(f"Error fetching transcript: {exc}")
        return None


def extract_video_id(video_url: str) -> str:
    if "/shorts" in video_url:
        return video_url.split("/")[-1]
    else:
        return parse_qs(urlparse(video_url).query)["v"][0]


if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=id1LEPLrp7c"
    print(get_youtube_transcript(video_url, ("fr",)))
