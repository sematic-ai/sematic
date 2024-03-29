import { NestedViewComponentType, ValueComponentType } from "src/typeViz/common";
import { S3BucketValueView, S3LocationValueView } from "src/typeViz/views/aws";
import BoolValueView from "src/typeViz/views/boolean";
import DataclassValueView, { DataclassElementsView } from "src/typeViz/views/dataclass";
import DataFrameValueView, { DataFrameDetailsView, DataFrameSummaryExpandedView, DataFrameSummaryView } from "src/typeViz/views/dataframetable";
import DatetimeValueView from "src/typeViz/views/datatime";
import DictValueView, { DictElementsView } from "src/typeViz/views/dict";
import EnumValueView from "src/typeViz/views/enum";
import FloatValueView from "src/typeViz/views/float";
import {
    HuggingFaceDatasetReferenceShortView,
    HuggingFaceDatasetReferenceValueView,
    HuggingFaceModelReferenceShortView,
    HuggingFaceModelReferenceValueView
} from "src/typeViz/views/HuggingFaceReference";
import { HuggingFaceStoredModelShortView, HuggingFaceStoredModelFullView } from "src/typeViz/views/HuggingFaceStoredModel";
import ImageValueView, { ImageExpandedView } from "src/typeViz/views/image";
import IntValueView from "src/typeViz/views/int";
import LinkValueView from "src/typeViz/views/link";
import PromptResponseCollapsedView, { PromptResponseExpandedView } from "src/typeViz/views/PromptResponse";
import ListValueView, { ListElementsView } from "src/typeViz/views/list";
import NoneValueView from "src/typeViz/views/none";
import PlotlyFigureValueView, { PlotlyFigureExpandedView } from "src/typeViz/views/plotly";
import { ReprExpandedView, ReprValueView } from "src/typeViz/views/repr";
import StrValueView from "src/typeViz/views/str";
import TorchDataLoaderValueView, { TorchDataFieldsView } from "src/typeViz/views/torchDataLoader";
import { TupleElementsView, TupleValueView } from "src/typeViz/views/tuple";
import ValueView, { ValueExpandedView } from "src/typeViz/views/value";
import UnionValueView from "src/typeViz/views/union";

export type RenderDetails = {
    value: ValueComponentType,
    nested?: NestedViewComponentType
}

// The Registry (fill data)
const meta: Array<[string, RenderDetails]> = [
    ["repr", { value: ReprValueView, nested: ReprExpandedView }],
    ["val", { value: ValueView, nested: ValueExpandedView }],
    ["NoneType", { value: NoneValueView }],
    ["float", { value: FloatValueView }],
    ["str", { value: StrValueView }],
    ["int", { value: IntValueView }],
    ["bool", { value: BoolValueView }],
    ["FloatInRange", { value: FloatValueView }],
    ["list", { value: ListValueView, nested: ListElementsView }],
    ["set", { value: ListValueView, nested: ListElementsView }],
    ["tuple", { value: TupleValueView, nested: TupleElementsView }],
    ["dict", { value: DictValueView, nested: DictElementsView }],
    ["dataclass", { value: DataclassValueView, nested: DataclassElementsView }],
    ["Union", { value: UnionValueView }],
    ["Link", { value: LinkValueView }],
    ["datetime.datetime", { value: DatetimeValueView }],
    ["enum.Enum", { value: EnumValueView }],
    ["plotly.graph_objs._figure.Figure", { value: PlotlyFigureValueView, nested: PlotlyFigureExpandedView }],
    ["torch.utils.data.dataloader.DataLoader", { value: TorchDataLoaderValueView, nested: TorchDataFieldsView }],
    ["matplotlib.figure.Figure", {value: ImageValueView, nested: ImageExpandedView}],
    ["pandas.core.frame.DataFrame", { value: DataFrameValueView, nested: DataFrameDetailsView }],
    ["DataFrameDataPreview", { value: DataFrameSummaryView, nested: DataFrameSummaryExpandedView }],
    ["DataFrameDataDescribe", { value: DataFrameSummaryView, nested: DataFrameSummaryExpandedView }],
    ["sematic.types.types.aws.s3.S3Bucket", { value: S3BucketValueView }],
    ["sematic.types.types.aws.s3.S3Location", { value: S3LocationValueView }],
    [
        "sematic.types.types.huggingface.stored_model.HuggingFaceStoredModel",
        {value: HuggingFaceStoredModelShortView, nested: HuggingFaceStoredModelFullView}
    ],
    [
        "sematic.types.types.huggingface.dataset_reference.HuggingFaceDatasetReference",
        {value: HuggingFaceDatasetReferenceShortView, nested: HuggingFaceDatasetReferenceValueView}
    ],
    [
        "sematic.types.types.huggingface.model_reference.HuggingFaceModelReference",
        {value: HuggingFaceModelReferenceShortView, nested: HuggingFaceModelReferenceValueView}
    ],
    ["sematic.types.types.image.Image", {value: ImageValueView, nested: ImageExpandedView}],
    ["sematic.types.types.prompt_response.PromptResponse", { value: PromptResponseCollapsedView, nested: PromptResponseExpandedView}],
];

export const TypeComponents = new Map<string, RenderDetails>();

meta.forEach(([key, value]) => {
    TypeComponents.set(key, value);
});