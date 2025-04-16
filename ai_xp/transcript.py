from typing import Any
import requests
import json
from dataclasses import dataclass, field

from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api._errors import YouTubeTranscriptApiException


@dataclass(kw_only=True, frozen=True)
class TranscriptSuccessResult:
    transcript: list[dict[str, Any]]

    @property
    def full_text(self) -> str:
        # An entry contains text, start and duration.
        return " ".join([entry["text"] for entry in self.transcript])  # type: ignore


@dataclass(kw_only=True, frozen=True)
class TranscriptErrorResult:
    error: YouTubeTranscriptApiException


def get_youtube_transcript(
    video_url: str,
    languages: tuple[str, ...] | str,
) -> TranscriptSuccessResult | TranscriptErrorResult:
    # ISO 639-1 language code
    languages = (languages,) if isinstance(languages, str) else languages
    video_id = extract_video_id(video_url)
    try:
        # Try preferred language. If the language is not available this will fail.
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)  # type: ignore
        return TranscriptSuccessResult(transcript=transcript)  # type: ignore
    except YouTubeTranscriptApiException as error:
        print(f"Error fetching transcript: {type(error).__name__}")
        return TranscriptErrorResult(error=error)


def extract_video_id(url: str) -> str | None:
    """Extrait l'ID de la vidéo YouTube avec les modules standards"""
    if not url:
        return None

    parsed = urlparse(url)

    if not parsed.netloc:
        # Assume the id was provided as is.
        return url

    if "youtu.be" in parsed.netloc:
        return parsed.path.split("/")[1].split("&")[0]

    if "youtube.com" in parsed.netloc:
        params = parse_qs(parsed.query)
        return params["v"][0] if "v" in params else parsed.path.split("/")[2]

    return None


if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=id1LEPLrp7c"
    print(get_youtube_transcript(video_url, ("fr",)))
