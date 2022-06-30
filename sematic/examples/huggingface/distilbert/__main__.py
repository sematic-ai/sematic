from transformers import TrainingArguments

from sematic.examples.huggingface.distilbert.pipeline import pipeline, PipelineConfig


TRAINING_ARGS = TrainingArguments(
    output_dir="test_trainer", evaluation_strategy="epoch"
)
PIPELINE_CONFIG = PipelineConfig


def main():
    pipeline(training_args=TRAINING_ARGS, config=PipelineConfig).set(
        name="HuggingFace DistilBERT Yelp Reviews Example",
        tags=["hugging-face", "example", "bert"],
    ).resolve()


if __name__ == "__main__":
    main()
