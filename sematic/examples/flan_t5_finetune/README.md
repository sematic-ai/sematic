# Fine-Tuning FLAN-T5 with LoRA

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

This example shows a simple Sematic pipeline which:

- Downloads and splits a HuggingFace
[dataset](https://huggingface.co/datasets/pacovaldez/pandas-documentation) 
containing sections of [pandas](https://pandas.pydata.org/) documentation
paired with summaries of that documentation.
- Fine-tunes a specified variant of FLAN-T5 using
[LoRA](https://arxiv.org/abs/2106.09685) (a mechanism to fine-tune LLMs while
leveraging far fewer free parameters in the tuning than are present in the original
model).
- Runs inference on the test data, displaying the results in Sematic.
- Exports the resulting fine-tined model to a HuggingFace repo of your choice.

This example only supports local execution. To run it:

- [install sematic](https://docs.sematic.dev/onboarding/get-started)
- `sematic start`
- `sematic run examples/flan_t5_finetune -- --help`
- If you see an ewrror about missing libraries, install them with the provided command.
- `sematic run examples/flan_t5_finetune -- --max-train-samples 1 --max-test-samples 1 --model-size small`
- View the pipeline results in the Sematic UI at `http://localhost:5001`.
- Change the configuration to the pipeline as desired. See the CLI help
with `sematic run examples/flan_t5_finetune -- --help` for options.

#### TODO: file ticket for remote-compatible hugging face type serializations
#### TODO: file ticket for remote-compatible hugging face type visualizations
#### TODO: file ticket for getting pytorch 1.13.1 working for Ray examples