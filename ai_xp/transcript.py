import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Self
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import FetchedTranscript, Transcript, YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    YouTubeTranscriptApiException,
)

from ai_xp.utils import load_json


@dataclass(frozen=True, kw_only=True)
class TranscriptPath:
    language_code: str
    source: str
    video_id: str
    title_slug: str
    status: str
    extension: str

    @classmethod
    def from_path(cls, path: Path | str) -> Self:
        language_code, source, video_id, title_slug, status, extension = Path(
            path
        ).name.split(".", maxsplit=6)
        return cls(
            language_code=language_code,
            source=source,
            video_id=video_id,
            title_slug=title_slug,
            status=status,
            extension=extension,
        )

    @classmethod
    def from_transcript(
        cls, transcript: FetchedTranscript, title_slug: str, extension: str
    ) -> Self:
        source = "generated" if transcript.is_generated else "manually_created"
        return cls(
            language_code=transcript.language_code,
            source=source,
            video_id=transcript.video_id,
            title_slug=title_slug,
            status="success",
            extension=extension,
        )

    def to_filename(self) -> str:
        return ".".join(
            (
                self.language_code,
                self.source,
                self.video_id,
                self.title_slug,
                self.status,
                self.extension,
            )
        )

    def asdict(self) -> dict[str, str]:
        return asdict(self)


def load_transcript_full_text(transcript_output_file_path: Path) -> str:
    # Load a JSON-serialized transcript.
    transcript_full_text = "\n".join(
        line["text"] for line in load_json(transcript_output_file_path)["snippets"]
    )
    return transcript_full_text


@dataclass(kw_only=True, frozen=True)
class TranscriptSuccessResult:
    transcript: FetchedTranscript

    def full_text(self) -> str:
        # An entry contains text, start and duration.
        return " ".join([entry["text"] for entry in self.transcript.to_raw_data()])  # type: ignore

    def full_text_multiple_lines(self) -> str:
        # An entry contains text, start and duration.
        return "\n".join([entry["text"] for entry in self.transcript.to_raw_data()])  # type: ignore

    def to_json_serializable(
        self, *, additional_metadata: dict[str, str] | None = None
    ) -> dict[str, Any]:
        data = {k: v for k, v in self.transcript.__dict__.items()}
        data["snippets"] = self.transcript.to_raw_data()
        if additional_metadata:
            data["metadata"] = additional_metadata
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_json_serializable(), ensure_ascii=False, indent=4)

    def generate_transcript_parsed_name(self, title_slug: str) -> TranscriptPath:
        return TranscriptPath.from_transcript(
            transcript=self.transcript, title_slug=title_slug, extension="json"
        )


@dataclass(kw_only=True, frozen=True)
class TranscriptErrorResult:
    error: Exception
    # error: YouTubeTranscriptApiException
    video_id: str

    def to_json(self) -> str:
        exc_name = type(self.error).__name__
        summary = str(self.error)
        obj = {"error": {"exc_name": exc_name, "summary": summary}}
        return json.dumps(obj, ensure_ascii=False, indent=4)

    def generate_transcript_parsed_name(self, title_slug: str) -> TranscriptPath:
        exc_name = type(self.error).__name__
        return TranscriptPath(
            language_code="_",
            source="_",
            video_id=self.video_id,
            title_slug=title_slug,
            status=exc_name,
            extension="json",
        )


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
    if not video_id:
        # This should not happen, the error cannot even be logged.
        raise ValueError
    try:
        # Try preferred language. If the language is not available this will fail.
        transcript = get_youtube_transcript_internal(
            video_id, preferred_languages
        ).fetch()
        return TranscriptSuccessResult(transcript=transcript)
    except YouTubeTranscriptApiException as error:
        print(f"Error fetching transcript: {type(error).__name__}")
        return TranscriptErrorResult(error=error, video_id=video_id)
    except TypeError as error:
        print(f"Error fetching transcript: {type(error).__name__}")
        return TranscriptErrorResult(error=error, video_id=video_id)


def get_youtube_transcript_internal(
    video_id: str,
    preferred_languages: tuple[str, ...] | str,
    *,
    try_translation: bool = True,
) -> Transcript:
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)
    try:
        result = transcript_list.find_transcript(preferred_languages)
        return result
    except YouTubeTranscriptApiException:
        if not try_translation:
            raise

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
                    "Translated transcript from "
                    f"{first_available_transcript.language_code} to {preferred_language}."
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
