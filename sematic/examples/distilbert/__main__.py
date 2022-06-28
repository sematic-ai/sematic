from sematic.examples.distilbert.pipeline import pipeline
from transformers import TrainingArguments

training_args = TrainingArguments(output_dir="test_trainer", evaluation_strategy="epoch")

def main():
    pipeline(training_args).set(
        name="HuggingFace DistilBERT Yelp Reviews Example", tags=["hugging-face", "example", "bert"]
    ).resolve()


if __name__ == "__main__":
    main()
