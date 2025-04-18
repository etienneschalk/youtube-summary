import json
from dataclasses import dataclass, field
from pathlib import Path
from time import sleep
from typing import Self

import pandas as pd

from ai_xp.scrapper import MetadataPath, YouTubeHtmlScrapper
from ai_xp.transcript import (
    TranscriptPath,
    extract_video_id,
    get_youtube_transcript,
)
from ai_xp.utils import render_title_slug, render_video_url
from ai_xp.youtube_history import YouTubeHistoryAnalyzer


@dataclass(kw_only=True, frozen=True)
class FileDatabase:
    input_lookup_dir_path: Path
    # Assumption: time independant
    # (refetching likely won't update metadata)
    # Run a reprocessing if this is absolutely needed.
    metadata_lookup_dir_path: Path
    # Assumption: time independant (refetching likely won't update transcript)
    # (refetching likely won't update metadata)
    # Run a reprocessing if this is absolutely needed.
    transcript_lookup_dir_path: Path
    # Assumption: time dependant: indeed, LLM as a function is completely
    # impure: each new run will lead to a different LLM outputs, even when the
    # input is exactly the same. Manually selecting between multiple outputs
    # might happen.
    llm_output_lookup_dir_path: Path
    input_dataframe: pd.DataFrame = field(repr=False)
    metadata_dataframe: pd.DataFrame = field(repr=False)
    transcript_dataframe: pd.DataFrame = field(repr=False)
    llm_output_dataframe: pd.DataFrame = field(repr=False)

    def refresh(self) -> Self:
        # XXX Inefficient. Just recreate a new instance. This is bruteforce
        return self.from_paths_detailed(
            input_lookup_dir_path=self.input_lookup_dir_path,
            metadata_lookup_dir_path=self.metadata_lookup_dir_path,
            transcript_lookup_dir_path=self.transcript_lookup_dir_path,
            llm_output_lookup_dir_path=self.llm_output_lookup_dir_path,
        )

    @classmethod
    def from_paths(
        cls,
        input_lookup_dir_path: Path,
        root_database_path: Path,
    ) -> Self:
        metadata_lookup_dir_path = root_database_path / "metadata_output"
        transcript_lookup_dir_path = root_database_path / "transcript_output"
        llm_output_lookup_dir_path = root_database_path / "llm_output"
        return cls.from_paths_detailed(
            input_lookup_dir_path=input_lookup_dir_path,
            metadata_lookup_dir_path=metadata_lookup_dir_path,
            transcript_lookup_dir_path=transcript_lookup_dir_path,
            llm_output_lookup_dir_path=llm_output_lookup_dir_path,
        )

    @classmethod
    def from_paths_detailed(
        cls,
        *,
        input_lookup_dir_path: Path,
        metadata_lookup_dir_path: Path,
        transcript_lookup_dir_path: Path,
        llm_output_lookup_dir_path: Path,
    ) -> Self:
        input_dataframe = inputs_dir_to_dataframe(input_lookup_dir_path)
        metadata_dataframe = metadata_dir_to_dataframe(metadata_lookup_dir_path)
        transcript_dataframe = transcripts_dir_to_dataframe(transcript_lookup_dir_path)
        llm_output_dataframe = llm_outputs_dir_dataframe(llm_output_lookup_dir_path)

        return cls(
            input_lookup_dir_path=input_lookup_dir_path,
            metadata_lookup_dir_path=metadata_lookup_dir_path,
            transcript_lookup_dir_path=transcript_lookup_dir_path,
            llm_output_lookup_dir_path=llm_output_lookup_dir_path,
            input_dataframe=input_dataframe,
            metadata_dataframe=metadata_dataframe,
            transcript_dataframe=transcript_dataframe,
            llm_output_dataframe=llm_output_dataframe,
        )

    def search(self, df: pd.DataFrame, value: str) -> pd.DataFrame:
        return search(df, value)

    def inputs_with_missing_metadata(self) -> pd.DataFrame:
        df = self.input_dataframe.drop(self.metadata_dataframe.index)
        return df

    def inputs_with_missing_transcripts(
        self, indexer: list[str] | None = None
    ) -> pd.DataFrame:
        indexer = indexer or []
        # The composite key is (language_code, source, video_id)
        # This method by default consider any existing transcript in any language
        # to be not missing
        # But by passing an indexer, one can select missing transcripts for a particular
        # language of source.
        # This functionality is aimed at a potential feature of generating
        # summaries in multiple languages.
        # indexer = []
        # indexer = ["en",]
        # indexer = ["en", "manually_created"]
        df = self.input_dataframe.drop(
            self.transcript_dataframe.loc[*indexer].index.get_level_values("video_id")
        )
        return df

    def fetch_missing_metadata(self, *, sleep_seconds: int = 2):
        # Note: no retry mechanism implemented.
        # If a fetch resulted in error, it will not be retried.
        # For advertisements or videos unavailable, this is OK
        # But for some other errors, it might be beneficial
        # to retry a video.
        self.metadata_lookup_dir_path.mkdir(exist_ok=True, parents=True)
        missing_metadata = self.inputs_with_missing_metadata()
        print("Start metadata fetching ")
        print(f"There is {len(self.input_dataframe)} inputs. ")
        print(f"There is {len(missing_metadata)} missing metadata files. ")
        for idx, video_id in enumerate(missing_metadata.index, 1):
            print(f"{idx}/{len(missing_metadata)}: {video_id}")
            scrapper = YouTubeHtmlScrapper.from_video_id(video_id)
            if scrapper is None:
                print(f"ERROR Failed to fetch metadata for {video_id}")
            else:
                self.fetch_one_metadata(video_id, scrapper)

            print(f"Sleep for {sleep_seconds} seconds...")
            sleep(sleep_seconds)

    def fetch_one_metadata(self, video_id: str, scrapper: YouTubeHtmlScrapper):
        metadata_parsed = MetadataPath.from_scrapper(scrapper, "json")
        output_filename = metadata_parsed.to_filename()
        output_path = self.metadata_lookup_dir_path / output_filename
        if metadata_parsed.status == "success":
            output_path.write_text(scrapper.to_json())
        elif metadata_parsed.status == "likely-video-unavailable":
            message = "ERROR Cannot extract description, video likely unavailable"
            print(message)
            output_path.write_text(json.dumps({"error": message}))
        elif metadata_parsed.status == "likely-an-advertisement":
            message = (
                "ERROR JSON cannot be parsed (Regexp can). Empirically, likely an ad."
            )
            print(message)
            output_path.write_text(json.dumps({"error": message}))
        print(f"OK Written {video_id} metadata to {output_path} ")
        print(f"status ({metadata_parsed.status})")

    def fetch_missing_transcripts(self, *, sleep_seconds: int = 2):
        # Note: no retry mechanism implemented.
        # If a fetch resulted in error, it will not be retried.
        # For advertisements or videos unavailable, this is OK
        # But for some other errors, it might be beneficial
        # to retry a video.
        self.transcript_lookup_dir_path.mkdir(exist_ok=True, parents=True)
        missing_transcripts = self.inputs_with_missing_transcripts()
        print("Start transcripts fetching ")
        print(f"There is {len(self.input_dataframe)} inputs. ")
        print(f"There is {len(missing_transcripts)} missing transcripts files. ")
        for idx, video_id in enumerate(missing_transcripts.index, 1):
            print(f"{idx}/{len(missing_transcripts)}: {video_id}")
            title = str(missing_transcripts.loc[video_id]["title"])
            self.fetch_one_transcript(video_id, title)
            print(f"Sleep for {sleep_seconds} seconds...")
            sleep(sleep_seconds)

    def fetch_one_transcript(self, video_id: str, title: str):
        video_url = render_video_url(video_id)
        result = get_youtube_transcript(video_url, preferred_languages=("fr", "en"))
        title_slug = render_title_slug(title)
        transcript_parsed_name = result.generate_transcript_parsed_name(title_slug)
        transcript_output_file_path = (
            self.transcript_lookup_dir_path / transcript_parsed_name.to_filename()
        )
        transcript_output_file_path.parent.mkdir(exist_ok=True, parents=True)
        transcript_output_file_path.write_text(result.to_json())
        print(
            f"[  OK] Written transcript file for [[{title}]] into {transcript_output_file_path}"
        )
        print(f"status ({transcript_parsed_name.status})")

    def find_missing_llm_outputs_candidates(
        self, indexers: list[tuple[str, str]], *, keep_successful_only: bool
    ) -> dict[tuple[str, str], pd.DataFrame]:
        db = self
        dfs = {}
        for indexer in indexers:
            # Preselect transcripts for a (language_code, source) couple.
            transcripts = db.transcript_dataframe.loc[indexer]
            # Get video ids for which both metadata and transcripts are available
            video_ids = db.metadata_dataframe.index.intersection(
                transcripts.index.get_level_values("video_id")
            )

            # Drop already found LLM outputs
            df = db.input_dataframe.drop(
                db.llm_output_dataframe
                # .loc[indexer]
                # # TODO eschalk LLM outputs will follow the transcript structure (localized)
                .index
            ).loc[video_ids]
            df["metadata_status"] = db.metadata_dataframe.loc[video_ids][["status"]]
            df["transcript_status"] = transcripts.loc[video_ids][["status"]]
            df["metadata_path"] = db.metadata_dataframe.loc[video_ids][["path"]]
            df["transcript_path"] = transcripts.loc[video_ids][["path"]]

            # Filter out unsuccessful statuses
            if keep_successful_only:
                df = df[
                    (df["metadata_status"] == "success")
                    & (df["transcript_status"] == "success")
                ]

            dfs[indexer] = df
        return dfs


def inputs_dir_to_dataframe(input_lookup_dir_path: Path) -> pd.DataFrame:
    all_json_videos = consolidate_input_json(input_lookup_dir_path)
    all_json_df = pd.DataFrame.from_dict(all_json_videos.values())

    watch_history_json_list = input_lookup_dir_path / "watch_history_json_list.txt"
    assert watch_history_json_list.is_file()
    paths = list(
        Path(el) for el in watch_history_json_list.read_text().strip().split("\n")
    )
    df_list: list[pd.DataFrame] = []
    for path in paths:
        analyzer = YouTubeHistoryAnalyzer.from_path(path, consolidate=True)
        # Reverse index so top = recent ; bottom = ancient
        normalized_df = analyzer.df[["video_id", "title"]].drop_duplicates("video_id")[
            ::-1
        ]
        df_list.append(normalized_df)
    histories_concat_df = (
        pd.concat([all_json_df, *df_list])
        .drop_duplicates(subset="video_id")
        .set_index("video_id")
    )
    return histories_concat_df


def llm_outputs_dir_dataframe(output_lookup_dir_path: Path) -> pd.DataFrame:
    consolidated = consolidate_output_files(output_lookup_dir_path)
    df = consolidated_to_output_dataframe(consolidated)
    return df


def consolidate_input_json(lookup_dir_path: Path):
    all_json_paths = sorted(lookup_dir_path.glob("*.json"))
    all_videos = [video for p in all_json_paths for video in json.loads(p.read_text())]

    for video in all_videos:
        # video["title_slug"] = render_title_slug(video["title"])
        identifier = extract_video_id(video["href"])
        video["video_id"] = identifier
        # video["href"] = render_video_url(identifier)
        del video["href"]

    all_videos_dict = {video["video_id"]: video for video in all_videos}
    return all_videos_dict


# Define a search function
def search_string(value: str, search: str) -> bool:
    return search.lower() in str(value).lower()


def search(df: pd.DataFrame, value: str) -> pd.DataFrame:
    # Search for the string 'al' in all columns
    mask = df.apply(lambda x: x.map(lambda s: search_string(s, value)))

    # Filter the DataFrame based on the mask
    filtered_df = df.loc[mask.any(axis=1)]

    return filtered_df


def consolidate_output_files(output_lookup_dir_path: Path) -> dict[str, list[Path]]:
    all_summary_paths = sorted(output_lookup_dir_path.glob("*/*.md"))
    all_summary_dict: dict[str, list[Path]] = {}
    for path in all_summary_paths:
        all_summary_dict.setdefault(path.parent.stem, []).append(path)
    return all_summary_dict


def consolidated_to_output_dataframe(
    consolidated: dict[str, list[Path]],
) -> pd.DataFrame:
    # TODO eschalk analyze output LLM path
    df = pd.DataFrame(
        [(k, vv.stem, vv) for k, v in consolidated.items() for vv in v],
        columns=["timestamp", "video_id", "output_path"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%dT%H-%M-%S-%f")
    df = df.set_index(["timestamp", "video_id"])

    return df


def metadata_dir_to_dataframe(metadata_lookup_dir_path: Path) -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {**MetadataPath.from_path(path).asdict(), "path": path}
            for path in sorted(metadata_lookup_dir_path.glob("*.json"))
        ]
    )
    if df.empty:
        # Set expected empty column
        df = pd.DataFrame(columns=MetadataPath.__annotations__.keys())
    return df.set_index("video_id")


def transcripts_dir_to_dataframe(transcript_lookup_dir_path: Path) -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {**TranscriptPath.from_path(path).asdict(), "path": path}
            for path in sorted(transcript_lookup_dir_path.glob("*.json"))
        ]
    )
    if df.empty:
        # Set expected empty column
        df = pd.DataFrame(columns=TranscriptPath.__annotations__.keys())
    return df.set_index(["language_code", "source", "video_id"])
