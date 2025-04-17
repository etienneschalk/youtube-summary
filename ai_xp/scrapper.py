import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Self

from bs4 import BeautifulSoup


@dataclass(frozen=True, kw_only=True)
class YouTubeHtmlScrapper:
    soup: BeautifulSoup
    # Regex courtesy of
    # https://stackoverflow.com/questions/1060616/how-can-regex-ignore-escaped-quotes-when-matching-strings
    string_extraction_pattern = r'"((?:\\\\|\\"|[^"])*+)"'

    @classmethod
    def from_path(cls, path: Path):
        soup = BeautifulSoup(path.read_text(), features="html.parser")
        return cls(soup=soup)

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
        return cls(soup=soup)

    def title(self) -> str:
        return str(self.soup.title.text).rstrip(" - YouTube")

    def short_description(self, *, mode: Literal["json", "regex"] = "json") -> str:
        script_text = self.soup.body.script.text.replace("\n", "")

        if mode == "regex":
            return self.try_to_extract_short_description_with_regex(script_text)
        elif mode == "json":
            obj = json.loads(script_text.lstrip("var ytInitialPlayerResponse = ")[:-1])
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
