# Hacker News Summarization

It fetches stories from Hacker News based on an input query and uses a LLM to summarize them and generates a HTML page of the stories fetched.

## ⚠️ Pre-requisits ⚠️

This example uses LLMs via API so you need to either have
* [OpenAI API](https://openai.com/blog/openai-api)
* [Cohere API](https://dashboard.cohere.ai/welcome/register)

## Usage

Arguments
- `--query` (required) : Search query. Example "llm", "generative AI"
- `--past-n-days`: Past N number of days to fetch stories for
- `--max-stories` : Number of stories you'd want to fetch from HN

### For Cohere
- `--cohere-model` : Model you want to use for text summarization.
- `--cohere-api-key` (required): API key
- `--cohere-max-tokens` : Max number of tokens

### For OpenAI
- `--openai-model` : Model you want to use for text summarization.
- `--openai-api-key` (required): API key
- `--openai-max-tokens` : Max number of tokens

### 
