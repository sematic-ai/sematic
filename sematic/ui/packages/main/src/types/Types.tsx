import { AnyTypeRepr } from "@sematic/common/src/types";
import BoolValueView from "src/types/boolean";
import {
  CommonValueViewProps,
  TypeComponents,
  ValueView,
  ValueViewProps,
} from "src/types/common";
import DataclassValueView from "src/types/dataclass";
import DataFrameValueView from "src/types/dataframetable";
import DatetimeValueView from "src/types/datatime";
import DictValueView from "src/types/dict";
import EnumValueView from "src/types/enum";
import FloatValueView from "src/types/float";
import ImageValueView from "src/types/image";
import IntValueView from "src/types/int";
import LinkValueView from "src/types/link";
import ListValueView from "src/types/list";
import NoneValueView from "src/types/none";
import PlotlyFigureValueView from "src/types/plotly";
import StrValueView from "src/types/str";
import TorchDataLoaderValueView from "src/types/torchDataLoader";
import TupleValueView from "src/types/tuple";
import { S3BucketValueView, S3LocationValueView } from "src/types/aws";
export { renderSummary } from "src/types/common";

// ValueComponent props
type GenerateValueViewProps<U> = U extends AnyTypeRepr
  ? ValueViewProps<U>
  : never;
type AllValueViewProps =
  | CommonValueViewProps
  | GenerateValueViewProps<AnyTypeRepr>;
type ExpandViewFunc<U> = U extends AllValueViewProps
  ? (props: U) => JSX.Element
  : never;

export type ComponentRenderDetails = {
  value: ExpandViewFunc<AllValueViewProps>;
};

// The Registry (fill data)
const meta: Array<[string, ComponentRenderDetails]> = [
  ["NoneType", { value: NoneValueView }],
  ["float", { value: FloatValueView }],
  ["str", { value: StrValueView }],
  ["int", { value: IntValueView }],
  ["bool", { value: BoolValueView }],
  ["FloatInRange", { value: FloatValueView }],
  ["list", { value: ListValueView }],
  ["tuple", { value: TupleValueView }],
  ["dict", { value: DictValueView }],
  ["dataclass", { value: DataclassValueView }],
  ["Union", { value: ValueView }],
  ["Link", { value: LinkValueView }],
  ["datetime.datetime", { value: DatetimeValueView }],
  ["enum.Enum", { value: EnumValueView }],
  [
    "torch.utils.data.dataloader.DataLoader",
    { value: TorchDataLoaderValueView },
  ],
  ["plotly.graph_objs._figure.Figure", { value: PlotlyFigureValueView }],
  [
    "pandas.core.frame.DataFrame",
    {
      value: DataFrameValueView,
    },
  ],
  [
    "sematic.types.types.aws.s3.S3Bucket",
    {
      value: S3BucketValueView,
    },
  ],
  [
    "sematic.types.types.aws.s3.S3Location",
    {
      value: S3LocationValueView,
    },
  ],
  [
    "sematic.types.types.image.Image",
    {
      value: ImageValueView,
    },
  ],
];

meta.forEach(([key, value]) => {
  TypeComponents.set(key, value);
});
