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


def extract_video_id(video_url: str) -> str:
    if "/shorts" in video_url:
        return video_url.split("/")[-1]
    else:
        return parse_qs(urlparse(video_url).query)["v"][0]


if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=id1LEPLrp7c"
    print(get_youtube_transcript(video_url, ("fr",)))
