# Standard Library
import argparse

# Sematic
from sematic import LocalRunner
from sematic.examples.hackernews_summarization.pipeline import (
    CohereConfig,
    HNFetchConfig,
    OpenAIConfig,
    pipeline,
)


def main():
    parser = argparse.ArgumentParser("Hacker News Summarization")
    parser.add_argument(
        "--query",
        action="store",
        help="Search query to filter stories",
        required=True,
    )

    parser.add_argument(
        "--past-n-days",
        type=int,
        action="store",
        default=1,
        help="Past N number of days to fetch Hacker News for",
        required=False,
    )

    parser.add_argument(
        "--max-stories",
        type=int,
        action="store",
        default=10,
        help="Number of stories you'd want to fetch from HN",
        required=False,
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        action="store",
        default=100,
        help="Max number of tokens",
        required=False,
    )

    parser.add_argument(
        "--cohere-model",
        type=str,
        action="store",
        default="command",
        help="Model you want to use for text summarization.",
        required=False,
    )

    parser.add_argument(
        "--cohere-api-key",
        type=str,
        action="store",
        help="API key for cohere",
        required=False,
    )

    parser.add_argument(
        "--openai-model",
        type=str,
        action="store",
        default="text-ada-001",
        help="Model you want to use for text summarization.",
        required=False,
    )

    parser.add_argument(
        "--openai-api-key",
        type=str,
        action="store",
        help="API key for openai",
        required=False,
    )

    args = parser.parse_args()

    if not args.openai_api_key and not args.cohere_api_key:
        raise ValueError("Required to pass either OpenAI API key or Cohere API key")
    if args.openai_api_key and args.cohere_api_key:
        raise ValueError("Please pass only one API key.")
    if args.openai_api_key:
        llm_config = OpenAIConfig(args.openai_api_key, args.openai_model, args.max_tokens)
    elif args.cohere_api_key:
        llm_config = CohereConfig(args.cohere_api_key, args.cohere_model, args.max_tokens)

    hn_config = HNFetchConfig(args.past_n_days, args.max_stories)
    query = args.query

    future = pipeline(query, hn_config, llm_config).set(name="HackerNews summary")
    LocalRunner().run(future)


if __name__ == "__main__":
    main()
