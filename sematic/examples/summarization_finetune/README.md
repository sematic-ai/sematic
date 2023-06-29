# Fine-Tuning Language Models with LoRA

This example shows a simple Sematic pipeline which:

- Downloads and splits a HuggingFace dataset containing contextual text paired
with a summary of that text. By default, uses the
[`cnn_dailymail`](https://huggingface.co/datasets/cnn_dailymail) dataset,
which contains news articles and summaries of those articles. However,
any dataset that has one column containing context and one column with a
summary of that text can be used.
- Fine-tunes the specified model using
[LoRA](https://arxiv.org/abs/2106.09685) (a mechanism to fine-tune LLMs while
leveraging far fewer free parameters in the tuning than are present in the original
model).
- Runs inference on the test data, displaying the results in Sematic.
- Exports the resulting fine-tined model to a HuggingFace repo of your choice.

## Models

### FLAN-T5

Google's [FLAN-T5](https://huggingface.co/google/flan-t5-base) model is
a sequence-to-sequence language model that has been shown to generalize well
to a variety of language tasks. Google has produced multiple variants of
this model, which make it ideal for scaling up your development workflow
from a "toy" version that runs on your laptop CPU to a fully-fledged LLM
that can achieve state-of-the-art performance.

The model variants are:

- **Flan-T5-Small**: 80M parameters
- **Flan-T5-Base**: 250M parameters
- **Flan-T5-Large**: 780M parameters
- **Flan-T5-XL**: 3B parameters
- **Flan-T5-XXL**: 11B parameters

### Execution

This example only supports local execution. To run it:

- [install sematic](https://docs.sematic.dev/onboarding/get-started)
- `sematic start`
- `sematic run examples/summaization_finetune -- --help`
- If you see an ewrror about missing libraries, install them with the provided command.
- `sematic run examples/summaization_finetune -- --max-train-samples 1 --max-test-samples 1 --model-size small`
- View the pipeline results in the Sematic UI at `http://localhost:5001`.
- Try a different dataset:

```
sematic run examples/summaization_finetune -- \
 --max-train-samples 1 \
 --max-test-samples 1 \
 --model-size small \
 --dataset amazon_us_reviews:Baby_v1_00 \
 --text-column review_body \
 --summary-column review_headline \
 --max-output-length 64
```

- Change the configuration to the pipeline as desired. See the CLI help
with `sematic run examples/summaization_finetune -- --help` for options.
