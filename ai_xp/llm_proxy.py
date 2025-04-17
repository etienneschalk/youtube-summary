from dataclasses import dataclass, field
import json
from pathlib import Path

import requests


@dataclass(kw_only=True, frozen=True)
class OpenRouterAiProxy:
    api_key: str = field(repr=False)
    # model: str = "deepseek/deepseek-chat-v3-0324:free"
    # model: str = "google/gemini-2.5-pro-exp-03-25:free"
    model: str = "deepseek/deepseek-r1:free"

    def prompt(self, user_content: str, assistant_content: str | None = None):
        messages = [
            {"role": "user", "content": user_content},
        ]
        if assistant_content is not None:
            messages.append(
                {"role": "assistant", "content": assistant_content},
            )

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": messages,
                }
            ),
        )
        response_dict = json.loads(response.content.decode())
        return response_dict
