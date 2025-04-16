from dataclasses import dataclass
from pathlib import Path
import re
from bs4 import BeautifulSoup


@dataclass(frozen=True, kw_only=True)
class YouTubeHtmlScrapper:
    soup: BeautifulSoup
    string_extraction_pattern = r'"((?:\\\\|\\"|[^"])*+)"'

    @classmethod
    def from_path(cls, path: Path):
        soup = BeautifulSoup(path.read_text(), features="html.parser")
        return cls(soup=soup)

    def title(self) -> str:
        return str(self.soup.title.text).rstrip(" - YouTube")

    def short_description(self) -> str:
        script_text = self.soup.body.script.text.replace("\n", "")

        # Regex courtesy of
        # https://stackoverflow.com/questions/1060616/how-can-regex-ignore-escaped-quotes-when-matching-strings
        shortDescription = (
            re.findall(
                r"shortDescription:\s+" + self.string_extraction_pattern, script_text
            )[0]
            .replace(r"\"", '"')
            .replace("\\n", "\n")
        )

        return shortDescription
