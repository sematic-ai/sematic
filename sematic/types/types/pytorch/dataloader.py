# Third-party
from torch.utils.data import DataLoader
from torch.utils.data.dataset import Dataset

# Sematic
from sematic.types.registry import SummaryOutput, register_to_json_encodable_summary
from sematic.types.serialization import get_json_encodable_summary


@register_to_json_encodable_summary(DataLoader)
def _data_loader_summary(value: DataLoader, _) -> SummaryOutput:
    return (
        dict(
            dataset=get_json_encodable_summary(value.dataset, Dataset),
            batch_size=value.batch_size,
            num_workers=value.num_workers,
            pin_memory=value.pin_memory,
            timeout=value.timeout,
        ),
        {},
    )
