# Standard Library
from io import BytesIO

# Third-party
import matplotlib.figure  # type: ignore
import matplotlib.pyplot as plt

# Sematic
from sematic.types.serialization import get_json_encodable_summary
from sematic.types.types.image import Image


def test_figure_summary():
    figure = plt.figure()
    plt.plot(range(100))

    figure_summary, figure_blobs = get_json_encodable_summary(
        figure, matplotlib.figure.Figure
    )

    file_obj = BytesIO()
    figure.savefig(file_obj)
    file_obj.flush()
    file_obj.seek(0)
    image = Image(bytes=file_obj.read())

    _, image_blobs = get_json_encodable_summary(image, Image)

    assert figure_summary["mime_type"] == "image/png"
    assert list(figure_blobs.values()) == list(image_blobs.values())
