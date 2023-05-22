# Standard Library
import os
from typing import List

# Third-party
from transformers import AutoModelForCausalLM, AutoTokenizer


def finetune_gptj():
    tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")
    with open(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "..", "..", "README.md"
        )
    ) as f:
        readme = f.read()
    print(len(tokenizer.encode(readme)))


finetune_gptj()
