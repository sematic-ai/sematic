# Third-party
import pandas as pd

# Sematic
from sematic import SilentResolver
from sematic.examples.lightning_resnet.checkpointing import SematicCheckpointIO
from sematic.examples.lightning_resnet.main import (
    LOCAL_DATA_CONFIG,
    LOCAL_EVAL_CONFIG,
    LOCAL_TRAINING_CONFIG,
)
from sematic.examples.lightning_resnet.pipeline import (
    PipelineResults,
    evaluate,
    pipeline,
    train,
)
from sematic.examples.lightning_resnet.train_eval import (
    EvaluationResults,
    plot_confusion,
)
from sematic.testing import mock_sematic_funcs
from sematic.types.types.aws.s3 import S3Location


def test_pipeline():
    # See https://docs.sematic.dev/diving-deeper/testing
    checkpointer = SematicCheckpointIO(
        s3_location=S3Location.from_uri("s3://fake/bucket")
    )
    with mock_sematic_funcs([train, evaluate]) as mocks:
        checkpoint = checkpointer.from_path("fake/checkpoint_location.ckpt")
        mocks[train].mock.return_value = checkpoint

        mock_eval_confusion_matrix = (
            pd.DataFrame(
                dict(
                    prediction=[0, 1, 2, 3, 4, 0, 0, 0, 0, 0],
                    label=[
                        0,
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                    ],
                    count=[2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                )
            )
            .pivot(index="prediction", columns="label", values="count")
            .fillna(0)
        )
        classes_list = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        mock_confusion_plot = plot_confusion(mock_eval_confusion_matrix, classes_list)
        mocks[evaluate].mock.return_value = EvaluationResults(
            accuracy=0.5,
            n_correct=10,
            n_samples=20,
            confusion_matrix_plot=mock_confusion_plot,
        )

        result = pipeline(
            train_config=LOCAL_TRAINING_CONFIG,
            data_config=LOCAL_DATA_CONFIG,
            eval_config=LOCAL_EVAL_CONFIG,
        ).resolve(resolver=SilentResolver())

        assert isinstance(result, PipelineResults)
        assert result.evaluation_results.accuracy == 0.5
        assert result.evaluation_results.confusion_matrix_plot == mock_confusion_plot
        assert result.final_checkpoint == checkpoint
