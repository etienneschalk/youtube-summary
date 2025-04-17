from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import FetchedTranscript, Transcript, YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    YouTubeTranscriptApiException,
)


@dataclass(kw_only=True, frozen=True)
class TranscriptSuccessResult:
    transcript: FetchedTranscript

    def full_text(self) -> str:
        # An entry contains text, start and duration.
        return " ".join([entry["text"] for entry in self.transcript.to_raw_data()])  # type: ignore

    def full_text_multiple_lines(self) -> str:
        # An entry contains text, start and duration.
        return "\n".join([entry["text"] for entry in self.transcript.to_raw_data()])  # type: ignore

    def to_json_serializable(self) -> dict[str, Any]:
        dico = {k: v for k, v in self.transcript.__dict__.items()}
        dico["snippets"] = self.transcript.to_raw_data()
        return dico

    def generate_path(self, title_slug: str) -> PurePosixPath:
        source = "generated" if self.transcript.is_generated else "manually_created"
        return PurePosixPath(
            f"{self.transcript.language_code}.{source}.{self.transcript.video_id}.{title_slug}.json"
            # f"{self.transcript.language_code}/{source}/{self.transcript.video_id}/{title_slug}.json"
        )


@dataclass(kw_only=True, frozen=True)
class TranscriptErrorResult:
    error: YouTubeTranscriptApiException


def get_youtube_transcript(
    video_url: str,
    preferred_languages: tuple[str, ...] | str,
) -> TranscriptSuccessResult | TranscriptErrorResult:
    # ISO 639-1 language code
    preferred_languages = (
        preferred_languages
        if isinstance(preferred_languages, tuple)
        else (preferred_languages,)
    )
    video_id = extract_video_id(video_url)
    try:
        # Try preferred language. If the language is not available this will fail.
        transcript = get_youtube_transcript_internal(
            video_id, preferred_languages
        ).fetch()
        return TranscriptSuccessResult(transcript=transcript)
    except YouTubeTranscriptApiException as error:
        print(f"Error fetching transcript: {type(error).__name__}")
        return TranscriptErrorResult(error=error)


def get_youtube_transcript_internal(
    video_id: str,
    preferred_languages: tuple[str, ...] | str,
) -> Transcript:
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)
    try:
        result = transcript_list.find_transcript(preferred_languages)
        return result
    except YouTubeTranscriptApiException:
        first_available_transcript = next(iter(transcript_list))
        print(first_available_transcript.language_code)
        available_translation_languages_codes = set(
            t.language_code for t in first_available_transcript.translation_languages
        )
        for preferred_language in preferred_languages:
            if preferred_language in available_translation_languages_codes:
                translated_transcript = first_available_transcript.translate(
                    preferred_language
                )
                result = translated_transcript
                print(
                    f"Translated transcript from {first_available_transcript.language_code} to {preferred_language}."
                )
                return result
        raise


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
