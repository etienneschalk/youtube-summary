import json
from dataclasses import asdict, dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Literal, Self

import pandas as pd
import requests

from ai_xp.scrapper import MetadataPath
from ai_xp.transcript import TranscriptPath, load_transcript_full_text
from ai_xp.utils import (
    load_json,
    load_toml,
    render_timestamp_slug,
    render_title_slug,
    render_video_url,
)

PromptsDictType = dict[Literal["user", "assistant", "family"], str]


class OpenRouterRateLimitExceeded(Exception):
    pass


@dataclass(frozen=True, kw_only=True)
class AiSummaryPath:
    prompt_family: str
    transcript_path_suffix: TranscriptPath

    @classmethod
    def from_transcript_path(
        cls, prompt_family: str, transcript_path_suffix: TranscriptPath
    ) -> Self:
        return cls(
            prompt_family=prompt_family,
            transcript_path_suffix=transcript_path_suffix,
        )

    @classmethod
    def from_path(cls, path: Path | str) -> Self:
        path = Path(path)
        prompt_family, suffix = path.name.split(".", maxsplit=1)
        transcript_path_suffix = TranscriptPath.from_path(suffix)
        return cls.from_transcript_path(prompt_family, transcript_path_suffix)

    def to_filename(self) -> str:
        return ".".join(
            (
                self.prompt_family,
                self.transcript_path_suffix.to_filename(),
            )
        )

    def asdict(self) -> dict[str, str]:
        return {
            "prompt_family": self.prompt_family,
            **self.transcript_path_suffix.asdict(),
        }


@dataclass(kw_only=True, frozen=True)
class OpenRouterAiProxy:
    api_key: str = field(repr=False)
    # model: str = "deepseek/deepseek-chat-v3-0324:free"
    # model: str = "google/gemini-2.5-pro-exp-03-25:free"
    model: str = "deepseek/deepseek-r1:free"

    def prompt(self, prompts: PromptsDictType):
        user_content = prompts["user"]
        assistant_content = prompts.get("assistant")

        messages = [
            {"role": "user", "content": user_content},
        ]
        if assistant_content is not None:
            messages.append(
                {"role": "assistant", "content": assistant_content},
            )

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": messages,
                }
            ),
        )
        response_dict = json.loads(response.content.decode())
        return response_dict


@dataclass(kw_only=True, frozen=True)
class VideoModel:
    video_id: str
    title: str | None
    description: str | None

    @property
    def title_slug(self) -> str | None:
        return render_title_slug(self.title) if self.title else None

    @property
    def video_url(self) -> str:
        return render_video_url(self.video_id)

    @property
    def best_prompt_family(self) -> str:
        if (self.title is not None) and (self.description is not None):
            return "basic_with_context"
        else:
            return "basic"

    @classmethod
    def from_path(cls, metadata_path: Path) -> Self:
        # Extract video_id from path itself.
        # Extract title and description from loaded JSON.
        metadata_json = load_json(Path(metadata_path))
        return cls(
            video_id=MetadataPath.from_path(metadata_path).video_id,
            title=metadata_json["title"],
            description=metadata_json["description"],
        )


@dataclass(kw_only=True, frozen=True)
class AiSummarizer:
    proxy: OpenRouterAiProxy
    all_prompts: dict[str, dict[str, PromptsDictType]]
    dry_run: bool
    creation_time: pd.Timestamp | None

    @cached_property
    def time_id(self) -> str | None:
        return render_timestamp_slug(self.creation_time) if self.creation_time else None

    @classmethod
    def instantiate(
        cls,
        proxy: OpenRouterAiProxy,
        dry_run: bool = False,
        prompts_path: Path = Path("resources/prompts/prompts.toml"),
        creation_time: pd.Timestamp | None = None,
    ):
        all_prompts = load_toml(prompts_path)["prompts"]
        return cls(
            proxy=proxy,
            all_prompts=all_prompts,
            dry_run=dry_run,
            creation_time=creation_time,
        )

    def summarize_with_ai(
        self,
        video: VideoModel,
        transcript_file_path: Path,
        llm_output_dir_path: Path,
        prompt_language_code: str,
        prompt_family: str | None,
    ) -> None:
        prompts = self.render_prompts(
            video, transcript_file_path, prompt_language_code, prompt_family
        )
        print(json.dumps(prompts, indent=4, ensure_ascii=False))
        self.prompt(prompts, transcript_file_path, llm_output_dir_path)

    def render_prompts(
        self,
        video: VideoModel,
        transcript_file_path: Path,
        prompt_language_code: str,
        prompt_family: str | None,
    ) -> PromptsDictType:
        print(f"Generating summary for transcript: {transcript_file_path}")

        if prompt_family is None:
            prompt_family = video.best_prompt_family

        prompts = self.get_prompts_for_language_and_family(
            prompt_language_code, prompt_family
        )

        transcript_full_text = load_transcript_full_text(transcript_file_path)

        prompts: PromptsDictType
        if prompt_family == "basic":
            prompts = {
                "user": prompts["user"].format(video_transcript=transcript_full_text),
                "assistant": prompts["assistant"],
                "family": prompt_family,
            }
            return prompts

        elif prompt_family == "basic_with_context":
            prompts = {
                "user": prompts["user"].format(
                    video_transcript=transcript_full_text,
                    video_title=video.title,
                    video_description=video.description,
                ),
                "assistant": prompts["assistant"],
                "family": prompt_family,
            }
            return prompts

        raise ValueError("Formatting for this prompt family is not supported yet.")

    def prompt(
        self,
        prompts: PromptsDictType,
        transcript_file_path: Path,
        llm_output_dir_path: Path,
    ) -> None:
        parsed_transcript_path = TranscriptPath.from_path(
            transcript_file_path.with_suffix(".md")
        )
        parsed_ai_summary_path = AiSummaryPath.from_transcript_path(
            prompts["family"], parsed_transcript_path
        )

        # Output the result into a time-identified subfolder.
        if self.time_id:
            llm_output_dir_path /= self.time_id

        llm_output_file_path = (
            llm_output_dir_path / parsed_ai_summary_path.to_filename()
        )

        if self.dry_run:
            print(
                f"[  OK] (DRY RUN) Would have written summary for {transcript_file_path} into {llm_output_file_path}"
            )
            return

        response = self.proxy.prompt(prompts)
        if "error" in response:
            print(json.dumps(response, indent=4))
            print(response["error"]["message"])
            # TODO eschalk refine error management, it can be something else than rate limit.
            raise OpenRouterRateLimitExceeded(response["error"]["message"])
        else:
            summary = response["choices"][0]["message"]["content"]
            llm_output_file_path.parent.mkdir(exist_ok=True, parents=True)
            llm_output_file_path.write_text(summary)
            print(
                f"[  OK] Written summary for {transcript_file_path} into {llm_output_file_path}"
            )

    def get_prompts_for_language_and_family(
        self, prompt_language_code: str, prompt_family: str
    ) -> PromptsDictType:
        prompts = self.all_prompts[prompt_family][prompt_language_code]
        return prompts
