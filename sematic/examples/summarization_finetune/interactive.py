# Standard Library
import time

# Third-party
import gradio as gr

# Sematic
from sematic.examples.summarization_finetune.train_eval import evaluate_single_text
from sematic.types import PromptResponse


def summarize(
    context,
    history,
    model,
    tokenizer,
    model_type,
    max_input_tokens,
    max_new_tokens,
    prompt_format,
):
    """Summarize the text given the model, and update the provided history.

    Parameters
    ----------
    context:
        The text to produce a summary for.
    history:
        A list of PromptResponse objects for all of the context/summary
        pairs that have been generated so far. Will be updated with the
        pair that is generated with this function call.
    model:
        The model to perform inference with.
    tokenizer:
        The tokenizer for the model.
    model_type:
        The kind of model (sequence to sequence or causal).
    max_input_tokens:
        The maximum number of tokens that can be used for the input.
    max_new_tokens:
        The maximum number of new tokens generated fot the output.
    prompt_format:
        The format of the prompt.

    Returns
    -------
    The summary of the context object.
    """
    prompt = prompt_format.extract_prompt(
        prompt_format.wrap_context(context), max_input_tokens
    )

    _, output_text = evaluate_single_text(
        model=model,
        tokenizer=tokenizer,
        model_type=model_type,
        max_new_tokens=max_new_tokens,
        eval_text=prompt,
    )

    summary = prompt_format.extract_summary(output_text)
    history.append(PromptResponse(context, summary))
    return summary


def launch_summary_app(
    model,
    tokenizer,
    model_type,
    max_input_tokens,
    max_new_tokens,
    prompt_format,
):
    """Launch an interactive Gradio app to generate summaries using the given model.

    Parameters
    ----------
    model:
        The model to run inference with.
    tokenizer:
        The tokenizer to use with the model.
    model_type:
        The kind of model (sequence to sequence or causal).
    max_input_tokens:
        The maximum number of tokens that can be used for the input.
    max_new_tokens:
        The maximum number of new tokens generated fot the output.
    prompt_format:
        The format of the prompt.

    Returns
    -------
    A transcript of all the context/summary pairs generated during the app session.
    """
    context = gr.Textbox()
    should_close = False
    history = []

    def close():
        nonlocal should_close
        should_close = True

    with gr.Blocks() as blocks:
        context = gr.Textbox(label="Context")
        summary = gr.Textbox(label="Summary")
        run_button = gr.Button("Run", variant="primary")
        stop_button = gr.Button("Stop", variant="secondary")
        run_button.click(
            lambda ctx: summarize(
                ctx,
                history,
                model,
                tokenizer,
                model_type,
                max_input_tokens,
                max_new_tokens,
                prompt_format,
            ),
            inputs=[context],
            outputs=[summary],
        )
        stop_button.click(lambda: close())

    blocks.launch(server_name="0.0.0.0", inbrowser=True, prevent_thread_lock=True)
    while not should_close:
        time.sleep(1)
    blocks.close()

    return history
