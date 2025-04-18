import json
from pathlib import Path

import pandas as pd

from ai_xp.database import FileDatabase
from ai_xp.llm_proxy import OpenRouterAiProxy
from ai_xp.transcript import (
    TranscriptSuccessResult,
    get_youtube_transcript,
)
from ai_xp.utils import (
    read_toml,
    render_timestamp_slug,
    render_title_slug,
    render_video_url,
    retrieve_api_key,
)


class OpenRouterRateLimitExceeded(Exception):
    pass


def main():
    dry_run = True
    dry_run = False
    with_ai_summary = False
    # with_ai_summary = True
    skip = (
        0  # argument to manually retrigger a failed run and restore cursor in the list.
    )
    print(f"{skip=}")
    slug_whitelist = []

    now = pd.Timestamp.now()
    time_id = render_timestamp_slug(now)
    # Assume that transcripts won't change and are "pure functions", unlike LLM outputs.
    transcript_output_dir_path = Path("generated") / "transcript_output"  # / time_id
    llm_output_dir_path = Path("generated") / "llm_output" / time_id
    if not dry_run:
        transcript_output_dir_path.mkdir(exist_ok=True, parents=True)
        llm_output_dir_path.mkdir(exist_ok=True, parents=True)

    inputs_lookup_dir_path = Path("inputs").resolve()
    outputs_lookup_dir_path = Path("generated/llm_output").resolve()
    db = FileDatabase.from_paths(inputs_lookup_dir_path, outputs_lookup_dir_path)
    videos_to_summarize = db.inputs_with_missing_outputs()

    for idx, (_, video_to_summarize) in enumerate(
        videos_to_summarize.reset_index().iterrows(), 1
    ):
        if skip > idx:
            continue

        # TODO eschalk read from metadata_output if missing?
        title = str(video_to_summarize["title"])
        href = str(video_to_summarize["href"])
        video_id = str(video_to_summarize["video_id"])
        timestamp = str(video_to_summarize["timestamp"])

        title_slug = render_title_slug(title)

        if slug_whitelist and title_slug not in slug_whitelist:
            print("Continue because not in whitelist")
            continue

        exc_name = videos_to_summarize.loc[video_id]["exc_name"]
        if is_unrecoverable_error(exc_name):
            print(
                f"[SKIP] {href} Continue because latest transcript query resulted in {exc_name} error."
            )
            continue

        # transcript_output_file_path = (
        #     transcript_output_dir_path / title_slug
        # ).with_suffix(f".{video_id}.txt")
        # llm_output_file_path = (llm_output_dir_path / title_slug).with_suffix(
        #     f".{video_id}.md"
        # )

        print(f"Handling {idx}/{len(videos_to_summarize)} [[{title}]]")
        if dry_run:
            print("Skip because dry run")
        else:
            print(f"Fetching transcript for video: {href} (output date: {timestamp})")
            handle_video(
                title,
                video_id,
                transcript_output_dir_path,
                llm_output_dir_path,
                with_ai_summary,
                now,
            )


def handle_video(
    title: str,
    video_id: str,
    transcript_output_dir_path: Path,
    llm_output_dir_path: Path,
    with_ai_summary: bool,
    now: pd.Timestamp,
) -> None:
    video_url = render_video_url(video_id)
    title_slug = render_title_slug(title)
    transcript_output_file_paths = sorted(
        transcript_output_dir_path.glob(f"*{video_id}*")
    )

    if not transcript_output_file_paths:
        result = get_youtube_transcript(video_url, preferred_languages=("fr", "en"))
        if isinstance(result, TranscriptSuccessResult):
            transcript_output_file_path = (
                transcript_output_dir_path
                / result.generate_transcript_parsed_name(title_slug)
            )
            transcript_output_file_path.parent.mkdir(exist_ok=True, parents=True)
            additional_metadata = {"creation_date": now.isoformat()}
            transcript_output_file_path.write_text(
                json.dumps(
                    result.to_json_serializable(
                        additional_metadata=additional_metadata
                    ),
                    ensure_ascii=False,
                    indent=4,
                )
            )
            print(
                f"[  OK] Written summary for [[{title}]] into {transcript_output_file_path}"
            )
            transcript_output_file_paths = [transcript_output_file_path]
        else:
            exc_name = type(result.error).__name__
            summary = f"<<<ERROR>>>: {exc_name}\n{str(result.error)}"
            error_output_file_path = (
                transcript_output_dir_path
                / result.generate_transcript_filename(title_slug)
            )
            error_output_file_path.write_text(summary)
            print(f"[ NOK] Written [[{title}]] into {error_output_file_path}")
            return

    transcript_output_file_path = transcript_output_file_paths[0]
    if with_ai_summary:
        # Re-read from file
        transcript_full_text = " ".join(
            line["text"]
            for line in json.loads(transcript_output_file_path.read_text())["snippets"]
        )
        # (language_code, transcript_source, video_id, title_slug, extension) = (
        #     transcript_output_file_path.name.split(".")
        # )
        api_key = retrieve_api_key()
        proxy = OpenRouterAiProxy(api_key=api_key)
        # TODO eschalk make the prompts configurable
        prompts_path = Path("resources/prompts/prompts.toml")
        available_prompts = read_toml(prompts_path)
        prompt = available_prompts["prompts"]["user"]["basic"]
        assistant_content = available_prompts["prompts"]["assistant"]["basic"]

        print(f"Generating summary for video: {video_url}")
        response = proxy.prompt(
            prompt.format(transcript=transcript_full_text), assistant_content
        )
        if "error" in response:
            print(json.dumps(response, indent=4))
            print(response["error"]["message"])
            raise OpenRouterRateLimitExceeded(response["error"]["message"])
        else:
            summary = response["choices"][0]["message"]["content"]
            llm_output_file_path = (
                llm_output_dir_path / transcript_output_file_path.with_suffix(".md")
            )
            llm_output_file_path.write_text(summary)
            print(f"[  OK] Written summary for [[{title}]] into {llm_output_file_path}")


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
