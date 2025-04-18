import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Self

from bs4 import BeautifulSoup

from ai_xp.transcript import extract_video_id
from ai_xp.utils import render_title_slug, render_video_url


@dataclass(frozen=True, kw_only=True)
class YouTubeHtmlScrapper:
    soup: BeautifulSoup
    url: str
    # Regex courtesy of
    # https://stackoverflow.com/questions/1060616/how-can-regex-ignore-escaped-quotes-when-matching-strings
    string_extraction_pattern = r'"((?:\\\\|\\"|[^"])*+)"'

    @classmethod
    def _from_path(cls, path: Path):
        soup = BeautifulSoup(path.read_text(), features="html.parser")
        return cls(soup=soup, url="")

    @classmethod
    def from_video_id(cls, video_id: str) -> Self | None:
        return cls.from_url(render_video_url(video_id))

    @classmethod
    def from_url(cls, url: str) -> Self | None:
        import requests

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad status codes
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch URL: {e}")
            return None

        soup = BeautifulSoup(response.text, features="html.parser")
        instance = cls(soup=soup, url=url)
        return instance

    def title(self) -> str:
        return str(self.soup.title.text).removesuffix(" - YouTube")

    def short_description(self, *, mode: Literal["json", "regex"] = "json") -> str:
        script_text = self.soup.body.script.text.replace("\n", "")

        if mode == "regex":
            return self.try_to_extract_short_description_with_regex(script_text)
        elif mode == "json":
            # Only works when fetching the HTML automatically, not manually from source.
            obj = json.loads(
                script_text.removeprefix("var ytInitialPlayerResponse = ")[:-1]
            )
            return obj["videoDetails"]["shortDescription"]

        raise NotImplementedError

    def try_to_extract_short_description_with_regex(self, script_text: str) -> str:
        patterns = [
            r'shortDescription":' + self.string_extraction_pattern,
            r"shortDescription:\s*" + self.string_extraction_pattern,
        ]
        for pattern in patterns:
            try:
                res = re.findall(pattern, script_text)[0]
                return res.replace("\\n", "\n")
            except IndexError:
                pass
        return ""

    def to_dict(self, *, mode: Literal["json", "regex"] = "json") -> dict[str, str]:
        return {"title": self.title(), "description": self.short_description(mode=mode)}

    def to_json(self, *, mode: Literal["json", "regex"] = "json") -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass(frozen=True, kw_only=True)
class MetadataPath:
    video_id: str
    title_slug: str
    status: str
    extension: str

    @classmethod
    def from_path(cls, path: Path | str) -> Self:
        video_id, title_slug, status, extension = Path(path).name.split(".", maxsplit=4)
        return cls(
            video_id=video_id, title_slug=title_slug, status=status, extension=extension
        )

    @classmethod
    def from_scrapper(
        cls,
        scrapper: YouTubeHtmlScrapper,
        extension: str,
    ) -> Self:
        video_id = extract_video_id(scrapper.url)
        if not video_id:
            # This should not happen, the error cannot even be logged.
            raise ValueError
        try:
            scrapper.short_description()
        except KeyError:
            return cls(
                video_id=video_id,
                title_slug="no_slug",
                status="likely-video-unavailable",
                extension=extension,
            )
        except json.decoder.JSONDecodeError:
            return cls(
                video_id=video_id,
                title_slug="no_slug",
                status="likely-an-advertisement",
                extension=extension,
            )

        title_slug = render_title_slug(scrapper.title())
        return cls(
            video_id=video_id,
            title_slug=title_slug,
            status="success",
            extension=extension,
        )

    def to_filename(self) -> str:
        return ".".join(
            (
                self.video_id,
                self.title_slug,
                self.status,
                self.extension,
            )
        )

    def asdict(self) -> dict[str, str]:
        return asdict(self)
