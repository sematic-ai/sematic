# Standard Library
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptResponse:
    """A language model prompt and the response to that prompt."""

    prompt: str
    response: str
