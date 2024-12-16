# Standard Library
import datetime
import logging
import os
import re
import time
import typing
from dataclasses import dataclass

# Third-party
import cohere
import openai
import requests
import trafilatura
from jinja2 import Template

# Sematic
import sematic


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


BASE_URL = "http://hn.algolia.com/api/v1/search"
COHERE = "cohere"
OPENAI = "openai"


@dataclass
class HNFetchConfig:
    past_n_days: int = 1
    max_stories: int = 10


@dataclass
class _LLMConfig:
    api_key: str
    model: str
    max_tokens: int
    _model_from: str


@dataclass
class CohereConfig(_LLMConfig):
    api_key: str
    model: str = "command"
    max_tokens: int = 100
    _model_from: str = COHERE


@dataclass
class OpenAIConfig(_LLMConfig):
    api_key: str
    model: str = "text-ada-001"
    max_tokens: int = 100
    _model_from: str = OPENAI


@dataclass
class Story:
    id: str
    created_at: str
    author: str
    title: str
    points: int
    text: typing.Optional[str] = None
    url: typing.Optional[str] = None
    summary: typing.Optional[str] = None


@sematic.func
def fetch_hn(
    query: str, hn_config: HNFetchConfig
) -> typing.List[typing.Dict[object, object]]:
    """
    # Fetches stories from HackerNews (https://news.ycombinator.com)

    ## Inputs
    - **query**: `str`. Search query
    - **hn_config**: Parameters to configure stories fetched from HackerNews

    ## Output
    - List of dict containing stories
    """
    timestamp = int(
        (
            datetime.datetime.today() - datetime.timedelta(days=hn_config.past_n_days)
        ).timestamp()
    )
    params = {
        "query": query,
        "tags": "story",
        "numericFilters": f"created_at_i>{timestamp}",
        "hitsPerPage": hn_config.max_stories,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        response_dict = response.json().get("hits")
        logger.info(f"Total fetched stories {len(response_dict)}")
        return response_dict
    except Exception as ex:
        logger.exception("Failed to fetch stories from HackerNews")
        raise ex


@sematic.func
def split_stories(
    stories: typing.List[typing.Dict[object, object]],
) -> typing.Dict[str, typing.List[Story]]:
    """
    # Split stories into stories that have text and into those that don't
    - Response coming from HackerNews contains stories that
        - have the story text (which will later be summarized)
        - don't have the text but a url pointing to the page that contains story text.
            - We will scrape the text from this url and then summarize the text

    ## Input
    - **stories**: list of response story dict

    ## Outputs
    - Dict containing `to_fetch` and `text_stories`
    """
    to_fetch_text_stories, text_stories = [], []
    for story_dict in stories:
        title = story_dict.get("title")
        story_text = story_dict.get("story_text")
        # @todo: add filter based on points?
        # we don't want ask HN stories
        if not re.search("Ask HN", title, re.IGNORECASE):
            story = Story(
                story_dict.get("objectID"),
                story_dict.get("created_at"),
                story_dict.get("author"),
                title,
                story_dict.get("points"),
                story_text,
                story_dict.get("url"),
            )
            if story_text:
                text_stories.append(story)
            # have only those stories that link to a story
            elif story.url:
                to_fetch_text_stories.append(story)
    logger.info(f"Stories containing story text: {len(text_stories)}")
    logger.info(f"Stories to fetch story text: {len(to_fetch_text_stories)}")
    return {"to_fetch": to_fetch_text_stories, "text_stories": text_stories}


@sematic.func
def scrape_story_text(stories: typing.List[Story]) -> typing.List[Story]:
    """
    # Scrape story text

    ## Input
    - **stories**: List of `Story` to scrape the text

    ## Output
    - List of `Story` containing scraped story text
    """
    fetched_stories = []
    for story in stories:
        url = story.url
        download = trafilatura.fetch_url(url)
        extracted_text = trafilatura.extract(download, include_comments=False)
        if extracted_text:
            story.text = extracted_text
            fetched_stories.append(story)
        else:
            logger.info(f"Unable to fetch story text from {story.url}")
    logger.info(f"Total stories to fetch: {len(stories)}")
    logger.info(f"Total fetched stories: {len(fetched_stories)}")
    return fetched_stories


@sematic.func
def summarize(stories: typing.List[Story], config: _LLMConfig) -> typing.List[Story]:
    """
    # Summarize a story with LLM
    - Supported provides: Cohere (cohere.com) and OpenAI (openai.com)
    - Depending on `config`, `summarize` will either call Cohere API or OpenAI API

    ## Inputs
    - **stories**: List of `Story` to summarize
    - **config**: LLMConfig

    ## Outoput
    - List of `Story` containing summary
    """

    def _cohere_llm() -> typing.List[Story]:
        summarized_stories = []
        co = cohere.Client(config.api_key)
        for i, story in enumerate(stories):
            time.sleep(15)  # cohere APIs are ratelimited to 5calls/min for free tier.
            try:
                response = co.generate(
                    model=config.model,
                    prompt=f"""
                        {story.text}\n\nTl;dr""",
                    max_tokens=config.max_tokens,
                    temperature=0.9,
                    k=0,
                    stop_sequences=[],
                    return_likelihoods="NONE",
                )
                summary = response.generations[0].text
                if summary:
                    story.summary = summary
                    summarized_stories.append(story)
            except Exception:
                logger.exception(f"Exception for {i}th story")
        return summarized_stories

    def _openai_llm() -> typing.List[Story]:
        summarized_stories = []
        openai.api_key = config.api_key
        for i, story in enumerate(stories):
            try:
                response = openai.Completion.create(
                    model=config.model,
                    prompt=f"""Summarize the prompt from HackerNews story
                     withing 3-5 sentences\n{story.text}""",
                    temperature=1,
                    max_tokens=config.max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=1,
                )
                summary = response.choices[0].text.strip()
                if summary:
                    story.summary = summary
                    summarized_stories.append(story)
            except Exception:
                logger.exception(f"Exception for {i}th story")
        return summarized_stories

    if config._model_from == COHERE:
        return _cohere_llm()
    elif config._model_from == OPENAI:
        return _openai_llm()


@sematic.func
def aggregate(
    summarized1: typing.List[Story], summarized2: typing.List[Story]
) -> typing.List[Story]:
    return [story for story in summarized1 + summarized2 if story.summary]


@sematic.func
def prepare_report_html(query: str, stories: typing.List[Story]) -> str:
    """
    # Generate HTML page with story summary

    ## Input
    - **stories**: List of `Story`

    ## Output
    - filepath of the html page
    """
    template = "sematic/examples/hackernews_summarization/template.html"
    with open(template) as f:
        template = Template(f.read())
    write_file = os.path.join(
        os.getcwd(), "sematic/examples/hackernews_summarization/report.html"
    )
    with open(write_file, "w") as f:
        f.write(template.render(query=query, stories=stories))
    return write_file


@sematic.func
def pipeline(query: str, hn_config: HNFetchConfig, llm_config: _LLMConfig) -> str:
    """
    # Fetch and summarize HackerNews articles for a given search query

    ## Inputs
    - **query**: Search query
    - **hn_config**: Parameters to configure stories fetched from HackerNews
    - **llm_config**: Parameters to configure LLM for summarization

    ## Output
    - Path the summary html page
    """
    stories_dict = fetch_hn(query, hn_config)
    preprocessed_op = split_stories(stories_dict)
    text_stories = preprocessed_op["text_stories"]
    to_fetch_text_stories = preprocessed_op["to_fetch"]

    summarized1 = summarize(text_stories, llm_config)

    fetched_stories = scrape_story_text(to_fetch_text_stories)
    summarized2 = summarize(fetched_stories, llm_config)

    stories = aggregate(summarized1, summarized2)
    return prepare_report_html(query, stories)
