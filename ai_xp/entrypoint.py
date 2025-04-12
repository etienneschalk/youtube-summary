import requests
import json
from dataclasses import dataclass, field
import pandas as pd
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

from ai_xp.database import FileDatabase
from ai_xp.llm_proxy import OpenRouterAiProxy
from ai_xp.transcript import TranscriptSuccessResult, get_youtube_transcript
from ai_xp.utils import read_toml, retrieve_api_key
from slugify import slugify


def main():
    dry_run = True
    dry_run = False
    skip = 48  # argument to manually retrigger a failed run and restore cursor in the list.
    skip = 29
    skip = 0
    print(f"{skip=}")
    slug_whitelist = ["clinical-psychologist-reviews-ai-therapists"]
    slug_whitelist = []

    now = pd.Timestamp.now()
    time_id = slugify(now.isoformat(), lowercase=False)
    output_dir_path = Path("generated") / "llm_output" / time_id
    if not dry_run:
        output_dir_path.mkdir(exist_ok=True, parents=True)

    inputs_lookup_dir_path = Path("resources/inputs").resolve()
    outputs_lookup_dir_path = Path("generated/llm_output").resolve()
    db = FileDatabase.from_paths(inputs_lookup_dir_path, outputs_lookup_dir_path)
    videos_to_summarize = db.inputs_with_missing_outputs()

    for idx, (_, video_to_summarize) in enumerate(
        videos_to_summarize.reset_index().iterrows(), 1
    ):
        if skip > idx:
            continue

        title = str(video_to_summarize["title"])
        href = str(video_to_summarize["href"])
        if "shorts" in href:
            print("Shorts not implemented yet, continue.")
            continue
        title_slug = slugify(title)

        if slug_whitelist and title_slug not in slug_whitelist:
            print("Continue because not in whitelist")
            continue

        output_file_path = (output_dir_path / title_slug).with_suffix(".md")

        print(f"Handling {idx}/{len(videos_to_summarize)} [[{title}]]")
        if dry_run:
            print("Skip because dry run")
        else:
            try:
                video_url = href
                print(f"Fetching transcript for video: {video_url}")
                result = get_youtube_transcript(
                    video_url, languages=("fr", "fr-FR", "en")
                )
                if isinstance(result, TranscriptSuccessResult):
                    api_key = retrieve_api_key()
                    proxy = OpenRouterAiProxy(api_key=api_key)
                    # TODO eschalk make the prompts configurable
                    prompts_path = Path("resources/prompts/prompts.toml")
                    available_prompts = read_toml(prompts_path)
                    prompt = available_prompts["prompts"]["user"]["basic"]
                    assistant_content = available_prompts["prompts"]["assistant"][
                        "basic"
                    ]
                    print(f"Generating summary for video: {video_url}")
                    response = proxy.prompt(
                        prompt.format(transcript=result.full_text), assistant_content
                    )
                    summary = response["choices"][0]["message"]["content"]
                    output_file_path.write_text(summary)

                    print(f"[ OK] Written [[{title}]] into {output_file_path}")
                else:
                    summary = f"<<<ERROR>>>: {type(result.error).__name__}\n{str(result.error)}"
                    error_output_file_path = output_file_path.with_suffix(".err.md")
                    error_output_file_path.write_text(summary)

                    print(f"[NOK] Written [[{title}]] into {error_output_file_path}")
            except RuntimeError as err:
                print("Skip because failure: " + str(err))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as exc:
        print()
        print("Script interrupted by user.")
