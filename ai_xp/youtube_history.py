from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Self
import pandas as pd

from matplotlib import pyplot as plt
from slugify import slugify
import xarray as xr
from dataclasses import dataclass
from pathlib import Path
import json
import pandas as pd
import xarray as xr
from matplotlib import pyplot as plt

from ai_xp.transcript import extract_video_id

path = Path(
    "/home/tselano/Downloads/takeout-20250416T125258Z-001/Takeout/YouTube et YouTube Music/historique/watch-history.json"
)


# @dataclass(frozen=True, kw_only=True)
# class YouTubeHistoryAnalyzer:
#     raw: list[dict[str, Any]]
#     # Regex courtesy of
#     # https://stackoverflow.com/questions/1060616/how-can-regex-ignore-escaped-quotes-when-matching-strings
#     string_extraction_pattern = r'"((?:\\\\|\\"|[^"])*+)"'

#     @classmethod
#     def from_path(cls, path: Path):
#         with open(path, "r") as fp:
#             history_json = json.load(fp)
#         return cls(raw=history_json)

#     def full_df(self) -> pd.DataFrame:
#         full_df = pd.DataFrame(history_json)
#         full_df["time"] = pd.to_datetime(full_df["time"], format="mixed")
#         full_df = full_df.sort_values(by="time")
#         full_df["timedelta"] = full_df["time"] - full_df["time"].iloc[0]
#         full_df = full_df.set_index("time")
#         return full_df

#     def df(self) -> pd.DataFrame:
#         return self.full_df().drop_duplicates(subset="titleUrl", keep="last")

#     def to_xarray(self) -> xr.Dataset:
#         df = self.df()
#         xds = xr.Dataset(
#             coords={
#                 "time": df.reset_index()["time"],
#             },
#             data_vars={
#                 "timedelta": ("time", df.reset_index()["timedelta"]),
#                 "href": ("time", df.reset_index()["titleUrl"]),
#             },
#         )

#         xds["views"] = xr.ones_like(xds["time"], dtype=int)
#         if not xds.time.indexes["time"].is_monotonic_increasing:
#             raise ValueError
#         return xds


# analyzer = YouTubeHistoryAnalyzer.from_path(path)


# daily_xds = xds.groupby("timedelta.days").sum()
# display(daily_xds)
# display(daily_xds.plot.scatter(x="days", y="views", marker="+"))
# display(daily_xds.plot.scatter(x="time", y="constant", marker="+"))


# Inspiration of https://stackoverflow.com/questions/45841786/creating-a-1d-heat-map-from-a-line-graph
# Think of a heat map as a 2 dimensional array with one row.


# daily_xds["views"].expand_dims({"rows": [0]}).plot.imshow(
#     cmap="plasma", size=4, aspect=5
# )
# plt.show()


# xds.groupby("timedelta.days").sum()["views"].expand_dims({"rows": [0]}).plot.imshow(
#     cmap="plasma", size=4, aspect=5
# )
# plt.show()


@dataclass
class YouTubeHistoryAnalyzer:
    """A class to load and analyze YouTube watch history data."""

    path: Path
    raw: list[dict[str, Any]]
    df: pd.DataFrame
    xds: xr.Dataset

    @classmethod
    def from_path(
        cls,
        path: Path | str,
        *,
        drop_url_duplicates: bool = True,
        lang: str = "fr",
        consolidate: bool = False,
    ) -> Self:
        """Create a YouTubeHistory instance from a JSON file path."""
        path = Path(path)

        # Load JSON data
        with open(path, "r") as fp:
            raw_history_json = json.load(fp)

        filtered_raw_history_json = raw_history_json

        # Consolidate history to add necessary data for transcript and summary logic
        if consolidate:
            filtered_raw_history_json = []
            for entry in raw_history_json:
                if "www.youtube.com" in entry["title"]:
                    entry["title"] = ""
                elif lang == "fr":
                    # Note: the prefix before the title must be found for all languages.
                    # If it is not french, the prefix will just be kept
                    entry["title"] = (
                        entry["title"].lstrip("Vous avez regardé ").lstrip("consulté ")
                    )
                else:
                    # Do nothing, the prefix will remain
                    pass
                entry["title_slug"] = slugify(entry["title"]) or "untitled"
                if "titleUrl" in entry:
                    if (
                        entry["titleUrl"].startswith("https://www.youtube.com/playlist")
                        or entry["titleUrl"].startswith("https://www.youtube.com/post")
                        or entry["titleUrl"] == "https://www.youtube.com/watch?v="
                        or "google.com/" in entry["titleUrl"]
                    ):
                        continue

                    identifier = extract_video_id(entry["titleUrl"])
                    if identifier:
                        entry["id"] = identifier
                        entry["href"] = "https://www.youtube.com/watch?v=" + identifier

                    filtered_raw_history_json.append(entry)

        # Create and preprocess DataFrame
        df = pd.DataFrame(filtered_raw_history_json)
        df["time"] = pd.to_datetime(df["time"], format="mixed")
        df = df.sort_values("time")
        if drop_url_duplicates:
            df = df.drop_duplicates(subset="titleUrl", keep="last")
        df["timedelta"] = df["time"] - df["time"].iloc[0]
        df = df.set_index("time")

        # Create xarray Dataset
        reset_df = df.reset_index()
        xds = xr.Dataset(
            coords={"time": reset_df["time"]},
            data_vars={
                "timedelta": ("time", reset_df["timedelta"].values),
                "href": ("time", reset_df["titleUrl"].values),
            },
        )
        xds["views"] = xr.ones_like(xds["time"], dtype=int)
        assert xds.time.indexes["time"].is_monotonic_increasing

        return cls(path=path, raw=raw_history_json, df=df, xds=xds)

    def group_by_days(self) -> xr.Dataset:
        """Group data by days and sum views."""
        return self.xds.groupby("timedelta.days").sum()

    def plot_daily_views(self, **kwargs) -> tuple[plt.Figure, plt.Axes]:
        """Plot daily views using a scatter plot."""
        daily_ds = self.group_by_days()
        return daily_ds.views.plot.scatter(x="days", y="views", marker="+", **kwargs)

    def plot_view_heatmap(
        self,
        cmap: str = "plasma",
        size: float = 4,
        aspect: float = 5,
    ) -> tuple[plt.Figure, plt.Axes]:
        """
        Create a heatmap visualization of viewing patterns.

        Inspiration of https://stackoverflow.com/questions/45841786/creating-a-1d-heat-map-from-a-line-graph
        Think of a heat map as a 2 dimensional array with one row.
        """
        daily_ds = self.group_by_days()
        expanded_view = daily_ds.views.expand_dims({"rows": [0]})

        return expanded_view.plot.imshow(cmap=cmap, aspect=aspect, size=size)

    def __repr__(self) -> str:
        return (
            f"YouTubeHistory:\n"
            f"- Path: {self.path}\n"
            f"- Time range: {self.xds.time[0].values} to {self.xds.time[-1].values}\n"
            f"- Total entries: {len(self.xds.time)}\n"
            f"- Total days: {len(self.group_by_days().days)}"
        )
