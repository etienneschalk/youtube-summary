import json
from pathlib import Path

import pandas as pd
from slugify import slugify

from ai_xp.database import FileDatabase
from ai_xp.llm_proxy import OpenRouterAiProxy
from ai_xp.transcript import TranscriptSuccessResult, get_youtube_transcript
from ai_xp.utils import read_toml, retrieve_api_key


class OpenRouterRateLimitExceeded(Exception):
    pass


def main():
    dry_run = True
    dry_run = False
    skip = (
        0  # argument to manually retrigger a failed run and restore cursor in the list.
    )
    print(f"{skip=}")
    slug_whitelist = ["clinical-psychologist-reviews-ai-therapists"]
    slug_whitelist = []

    now = pd.Timestamp.now()
    time_id = slugify(now.isoformat(), lowercase=False)
    output_dir_path = Path("generated") / "llm_output" / time_id
    if not dry_run:
        output_dir_path.mkdir(exist_ok=True, parents=True)

    inputs_lookup_dir_path = Path("inputs").resolve()
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
        video_id = str(video_to_summarize["id"])
        timestamp = str(video_to_summarize["timestamp"])

        title_slug = slugify(title) or "untitled"

        if slug_whitelist and title_slug not in slug_whitelist:
            print("Continue because not in whitelist")
            continue

        exc_name = videos_to_summarize.loc[video_id]["exc_name"]
        if is_unrecoverable_error(exc_name):
            print(
                f"[SKIP] {href} Continue because latest transcript query resulted in {exc_name} error."
            )
            continue

        output_file_path = (output_dir_path / title_slug).with_suffix(".md")

        print(f"Handling {idx}/{len(videos_to_summarize)} [[{title}]]")
        if dry_run:
            print("Skip because dry run")
        else:
            try:
                print(
                    f"Fetching transcript for video: {href} (output date: {timestamp})"
                )
                # TODO eschalk autodectect language
                result = get_youtube_transcript(href, preferred_languages=("fr", "en"))
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
                    print(f"Generating summary for video: {href}")
                    response = proxy.prompt(
                        prompt.format(transcript=result.full_text), assistant_content
                    )
                    if "error" in response:
                        print(json.dumps(response, indent=4))
                        print(response["error"]["message"])
                        raise OpenRouterRateLimitExceeded(response["error"]["message"])
                    else:
                        summary = response["choices"][0]["message"]["content"]
                        output_file_path.write_text(summary)
                        print(f"[  OK] Written [[{title}]] into {output_file_path}")
                else:
                    exc_name = type(result.error).__name__
                    summary = f"<<<ERROR>>>: {exc_name}\n{str(result.error)}"
                    error_output_file_path = output_file_path.with_suffix(
                        f".{exc_name}.err.md"
                    )
                    error_output_file_path.write_text(summary)

                    print(f"[ NOK] Written [[{title}]] into {error_output_file_path}")
            except RuntimeError as err:
                print("Skip because failure: " + str(err))


def is_unrecoverable_error(exc_name: str) -> bool:
    errnames = ["TranscriptsDisabled", "NoTranscriptFound"]

    # TODO eschalk NoTranscriptFound can maybe fixed by improving the transcript lang filtering.
    for errname in errnames:
        if exc_name == errname:
            return True
    return False


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Script interrupted by user.")
