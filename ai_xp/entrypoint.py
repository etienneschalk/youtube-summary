import requests
import json
from dataclasses import dataclass, field
import pandas as pd
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

from ai_xp.llm_proxy import OpenRouterAiProxy
from ai_xp.transcript import get_youtube_transcript
from ai_xp.utils import read_toml, retrieve_api_key
from slugify import slugify


def summarize_youtube_video(video_url: str) -> str:
    print(f"Fetching transcript for video: {video_url}")
    transcript = get_youtube_transcript(video_url, languages=("fr", "en"))
    if not transcript:
        raise RuntimeError("Could not retrieve transcript")

    api_key = retrieve_api_key()
    proxy = OpenRouterAiProxy(api_key=api_key)

    # TODO eschalk make the prompts configurable
    prompts_path = Path("resources/prompts/prompts.toml")
    available_prompts = read_toml(prompts_path)
    prompt = available_prompts["prompts"]["user"]["basic"]
    assistant_content = available_prompts["prompts"]["assistant"]["basic"]
    print(f"Generating summary for video: {video_url}")
    response = proxy.prompt(prompt.format(transcript=transcript), assistant_content)
    summary = response["choices"][0]["message"]["content"]
    return summary


def main():
    dry_run = True
    dry_run = False
    skip = 48  # argument to manually retrigger a failed run and restore cursor in the list.
    skip = 112

    time_id = pd.Timestamp.now().isoformat()
    output_dir_path = Path("generated") / "llm_output" / time_id
    if not dry_run:
        output_dir_path.mkdir(exist_ok=True, parents=True)

    videos_to_summarize = json.loads(
        Path("resources/inputs/2025-04-06.json").read_text()
    )
    for idx, video_to_summarize in enumerate(videos_to_summarize, 1):
        if skip >= idx:
            continue
        title = video_to_summarize["title"]
        href = video_to_summarize["href"]
        if "shorts" in href:
            print("Shorts not implemented yet, continue.")
            continue
        title_slug = slugify(title)

        output_file_path = (output_dir_path / title_slug).with_suffix(".md")

        print(f"Handling {idx}/{len(videos_to_summarize)} [[{title}]]")
        if dry_run:
            print("Skip because dry run")
        else:
            try:
                result = summarize_youtube_video(href)
                output_file_path.write_text(result)
                print(f"Written [[{title}]] into {output_file_path}")
            except RuntimeError as err:
                print("Skip because failure: " + str(err))


if __name__ == "__main__":
    main()
