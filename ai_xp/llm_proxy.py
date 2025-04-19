import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import requests

from ai_xp.transcript import load_transcript_full_text
from ai_xp.utils import load_toml, render_title_slug, render_video_url

PromptsDictType = dict[Literal["user", "assistant"], str]


class OpenRouterRateLimitExceeded(Exception):
    pass


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


@dataclass(kw_only=True, frozen=True)
class AiSummarizer:
    proxy: OpenRouterAiProxy
    all_prompts: dict[str, dict[str, PromptsDictType]]

    @classmethod
    def instantiate(
        cls,
        proxy: OpenRouterAiProxy,
        prompts_path: Path = Path("resources/prompts/prompts.toml"),
    ):
        all_prompts = load_toml(prompts_path)["prompts"]
        return cls(proxy=proxy, all_prompts=all_prompts)

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
            }
            return prompts

        raise ValueError("Formatting for this prompt family is not supported yet.")

    def prompt(
        self,
        prompts: PromptsDictType,
        transcript_file_path: Path,
        llm_output_dir_path: Path,
    ) -> None:
        response = self.proxy.prompt(prompts)
        if "error" in response:
            print(json.dumps(response, indent=4))
            print(response["error"]["message"])
            # TODO eschalk refine error management, it can be something else than rate limit.
            raise OpenRouterRateLimitExceeded(response["error"]["message"])
        else:
            summary = response["choices"][0]["message"]["content"]
            llm_output_file_path = (
                llm_output_dir_path / transcript_file_path.with_suffix(".md")
            )
            llm_output_file_path.write_text(summary)
            print(
                f"[  OK] Written summary for {transcript_file_path} into {llm_output_file_path}"
            )

    def get_prompts_for_language_and_family(
        self, prompt_language_code: str, prompt_family: str
    ) -> PromptsDictType:
        prompts = self.all_prompts[prompt_family][prompt_language_code]
        return prompts
