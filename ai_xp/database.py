from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Self

import pandas as pd
from slugify import slugify

from ai_xp.transcript import extract_video_id


@dataclass(kw_only=True, frozen=True)
class FileDatabase:
    inputs_lookup_dir_path: Path
    outputs_lookup_dir_path: Path
    inputs_dataframe: pd.DataFrame = field(repr=False)
    outputs_dataframe: pd.DataFrame = field(repr=False)

    @classmethod
    def from_paths(
        cls, inputs_lookup_dir_path: Path, outputs_lookup_dir_path: Path
    ) -> Self:
        return cls(
            inputs_lookup_dir_path=inputs_lookup_dir_path,
            outputs_lookup_dir_path=outputs_lookup_dir_path,
            inputs_dataframe=inputs_dataframe(inputs_lookup_dir_path),
            outputs_dataframe=outputs_dataframe(outputs_lookup_dir_path),
        )

    def search(self, df: pd.DataFrame, value: str) -> pd.DataFrame:
        return search(df, value)

    def inputs_with_missing_outputs(self, keep: str = "last") -> pd.DataFrame:
        mask = ~self.inputs_dataframe["title_slug"].isin(
            self.outputs_dataframe.reset_index(level="title_slug")[
                "title_slug"
            ].unique()
        )
        out_df = self.inputs_dataframe[mask]
        errors_df_of_interest = (
            self.get_errors_df()
            .reset_index()
            .drop_duplicates(
                subset="title_slug", keep=keep
            )  # keep last by default because it is the most recent error.
            .loc[
                self.get_errors_df()
                .reset_index()["title_slug"]
                .isin(out_df["title_slug"])
            ]
        )
        final_df = pd.merge(
            out_df.reset_index(), errors_df_of_interest, how="left", on="title_slug"
        ).set_index(["id"])
        # ).set_index(["timestamp", "id", "title_slug"])
        return final_df
        # self.get_errors_df().reset_index().drop_duplicates(
        #     subset="title_slug", keep="last"
        # )[["title_slug", "exc_name"]]

        # self.get_errors_df().loc[out_df["title_slug"]]
        # out_df["exc_name"] = self.get_errors_df()[mask]["exc_name"]
        # return out_df

    def get_error_mask(self) -> pd.DataFrame:
        return self.outputs_dataframe.index.get_level_values("title_slug").str.endswith(
            ".err"
        )

    def get_success_df(self) -> pd.DataFrame:
        error_mask = self.get_error_mask()
        df = self.outputs_dataframe.loc[~error_mask]
        return df

    def get_errors_df(self) -> pd.DataFrame:
        error_mask = self.get_error_mask()
        errors_df = self.outputs_dataframe.loc[error_mask].reset_index()
        split_df = (
            errors_df["title_slug"]
            .str.split(".", n=2, expand=True)
            .rename(dict(zip(range(3), ["title_slug", "exc_name", "suffix"])), axis=1)
        )
        errors_df["title_slug"] = split_df["title_slug"]
        errors_df["exc_name"] = split_df["exc_name"]
        errors_df = errors_df.set_index(["timestamp", "title_slug"])
        return errors_df


def inputs_dataframe(inputs_lookup_dir_path: Path) -> pd.DataFrame:
    all_videos = consolidate_input_json(inputs_lookup_dir_path)
    df = pd.DataFrame.from_dict(all_videos.values()).set_index(["id"])
    return df


def outputs_dataframe(outputs_lookup_dir_path: Path) -> pd.DataFrame:
    consolidated = consolidate_output_files(outputs_lookup_dir_path)
    df = consolidated_to_output_dataframe(consolidated)
    return df


def consolidate_input_json(lookup_dir_path: Path):
    all_json_paths = sorted(lookup_dir_path.glob("*.json"))
    all_videos = [video for p in all_json_paths for video in json.loads(p.read_text())]

    for video in all_videos:
        video["title_slug"] = slugify(video["title"]) or "untitled"
        identifier = extract_video_id(video["href"])
        video["id"] = identifier
        video["href"] = "https://www.youtube.com/watch?v=" + identifier

    all_videos_dict = {video["id"]: video for video in all_videos}
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


def consolidate_output_files(outputs_lookup_dir_path: Path) -> dict[str, list[Path]]:
    all_summary_paths = sorted(outputs_lookup_dir_path.glob("*/*.md"))
    all_summary_dict: dict[str, list[Path]] = {}
    for path in all_summary_paths:
        all_summary_dict.setdefault(path.parent.stem, []).append(path)
    return all_summary_dict


def consolidated_to_output_dataframe(
    consolidated: dict[str, list[Path]],
) -> pd.DataFrame:
    df = pd.DataFrame(
        [(k, vv.stem, vv) for k, v in consolidated.items() for vv in v],
        columns=["timestamp", "title_slug", "output_path"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%dT%H-%M-%S-%f")
    df = df.set_index(["timestamp", "title_slug"])

    return df
