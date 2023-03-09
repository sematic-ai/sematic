import { AliasTypeRepr, BaseTypeRepr, CommonValueViewProps, ValueView, ValueViewProps } from "./common";
import EnumValueView from "./enum";
import DatetimeValueView from "./datatime";
import LinkValueView from "./link";
import DataFrameValueView from "./dataframetable";
import MatplotlibFigureValueView from "./matplot";
import PlotlyFigureValueView from "./plotly";
import TorchDataLoaderValueView from "./torchDataLoader";
import BoolValueView from "./boolean";
import DictValueView from "./dict";
import DataclassValueView, { DataclassTypeRepr } from "./dataclass";
import TupleValueView from "./tuple";
import ListValueView  from "./list";
import NoneValueView from "./none";
import IntValueView from "./int";
import FloatValueView from "./float";
import StrValueView from "./str";
import { TypeComponents, SpecificTypeSerialization } from "./common";
export {renderSummary} from "./common";


// TypeRepr types
export type AnyTypeRepr =
  BaseTypeRepr
  | AliasTypeRepr
  | DataclassTypeRepr

// TypeSerialization types
type GenerateTypeSerializationType<U> = U extends AnyTypeRepr ? SpecificTypeSerialization<U> : never; 
export type AnyTypeSerialization = GenerateTypeSerializationType<AnyTypeRepr>;

// ValueComponent props
type GenerateValueViewProps<U> = U extends AnyTypeRepr ? ValueViewProps<U> : never;
type AllValueViewProps = CommonValueViewProps | GenerateValueViewProps<AnyTypeRepr>;
type ExpandViewFunc<U> = U extends AllValueViewProps ? (props: U) => JSX.Element : never;

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
  [
    "plotly.graph_objs._figure.Figure",
    { value: PlotlyFigureValueView },
  ],
  [
    "matplotlib.figure.Figure",
    { value: MatplotlibFigureValueView },
  ],
  [
    "pandas.core.frame.DataFrame",
    {
      value: DataFrameValueView,
    },
  ],
];


meta.forEach(([key, value]) => {
  TypeComponents.set(key, value);
});

