import { AliasTypeRepr, BaseTypeRepr, CommonValueViewProps, ValueView, ValueViewProps } from "./common";
import EnumValueView from "./enum";
import DatetimeValueView from "./datatime";
import LinkValueView from "./link";
import DataFrameValueView from "./dataframetable";
import MatplotlibFigureValueView from "./matplot";
import PlotlyFigureValueView from "./plotly";
import TorchDataLoaderValueView from "src/types/torchDataLoader";
import BoolValueView from "./boolean";
import DictValueView from "./dict";
import DataclassValueView, { DataclassTypeRepr } from "./dataclass";
import TupleValueView from "./tuple";
import ListValueView  from "./list";
import NoneValueView from "./none";
import IntValueView from "./int";
import FloatValueView from "./float";
import StrValueView from "./str";
import { S3BucketValueView, S3LocationValueView } from "./aws";
import { ImageValueView } from "src/types/image";
import { TypeComponents, SpecificTypeSerialization } from "./common";


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

<<<<<<< HEAD
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
=======
interface TypeViewProps {
  typeRepr: TypeRepr;
}

function TypeView(props: TypeViewProps) {
  let repr = props.typeRepr;
  if (repr[0] === "class") {
    return (
      <code>
        {repr[2]["import_path"]}.{repr[1]}
      </code>
    );
  }
  return (
    <code>
      {repr[1]}
      {Object.keys(repr[2]).length > 0 && "[" + JSON.stringify(repr[2]) + "]"}
    </code>
  );
}

export function renderType(typeRepr: TypeRepr): JSX.Element {
  let componentPair = getComponentPair(typeRepr);

  if (componentPair) {
    let TypeViewComponent = componentPair.type;
    return <TypeViewComponent typeRepr={typeRepr} />;
  }

  return <TypeView typeRepr={typeRepr} />;
}

interface ValueViewProps {
  typeRepr: TypeRepr;
  typeSerialization: TypeSerialization;
  valueSummary: any;
  key?: string;
}

function ValueView(props: ValueViewProps) {
  return <code>{JSON.stringify(props.valueSummary)}</code>;
}

export function renderSummary(
  typeSerialization: TypeSerialization,
  valueSummary: any,
  typeRepr?: TypeRepr,
  key?: string
): JSX.Element {
  typeRepr = typeRepr || typeSerialization.type;

  let typeKey = typeRepr[1];
  let componentPair = getComponentPair(typeRepr);

  if (componentPair) {
    let ValueViewComponent = componentPair.value;
    return (
      <ValueViewComponent
        key={key}
        typeRepr={typeRepr}
        typeSerialization={typeSerialization}
        valueSummary={valueSummary}
      />
    );
  }

  // I don't know why this needs to be done, typeSerialization.registry is supposed to
  // be a TypeRegistry already :shrug:.
  let typeRegistry: TypeRegistry = new Map(
    Object.entries(typeSerialization.registry)
  );
  let parentTypes = typeRegistry.get(typeKey);

  if (parentTypes && parentTypes.length > 0) {
    return renderSummary(typeSerialization, valueSummary, parentTypes[0], key);
  }

  if (valueSummary["repr"] !== undefined) {
    return (
      <ReprValueView
        typeRepr={typeRepr}
        typeSerialization={typeSerialization}
        valueSummary={valueSummary}
        key={key}
      />
    );
  }

  return (
    <ValueView
      typeRepr={typeRepr}
      typeSerialization={typeSerialization}
      valueSummary={valueSummary}
      key={key}
    />
  );
}

function ReprValueView(props: ValueViewProps) {
  return <pre>{props.valueSummary["repr"]}</pre>;
}

function StrValueView(props: ValueViewProps) {
  return (
    <Typography component="div">
      <pre>"{props.valueSummary}"</pre>
    </Typography>
  );
}

function FloatValueView(props: ValueViewProps) {
  return (
    <Typography display="inline" component="span">
      {Number.parseFloat(props.valueSummary).toFixed(4)}
    </Typography>
  );
}

function IntValueView(props: ValueViewProps) {
  return (
    <Typography display="inline" component="span">
      {props.valueSummary}
    </Typography>
  );
}

function BoolValueView(props: ValueViewProps) {
  let value: boolean = props.valueSummary;
  return (
    <Chip
      label={value ? "TRUE" : "FALSE"}
      color={value ? "success" : "error"}
      variant="outlined"
      size="small"
    />
  );
}

function NoneValueView(props: ValueViewProps) {
  return <Chip label="NONE" size="small" />;
}

function ListValueView(props: ValueViewProps) {
  let typeRepr = props.typeRepr as AliasTypeRepr;
  if (!typeRepr[2].args) {
    return <Alert severity="error">Incorrect type serialization</Alert>;
  }

  let elementTypeRepr: TypeRepr = typeRepr[2].args[0].type as TypeRepr;
  const summaryIsEmpty = props.valueSummary["summary"].length === 0;

  const summaryIsComplete =
    props.valueSummary["summary"].length === props.valueSummary["length"];

  var summary;
  if (summaryIsEmpty) {
    summary = (
      <Typography display="inline" component="span" fontStyle={"italic"}>
        Nothing to display
      </Typography>
    );
  } else {
    summary = (
      <Typography display="inline" component="span">
        [
        {Array.from(props.valueSummary["summary"])
          .map<React.ReactNode>((element, index) =>
            renderSummary(
              props.typeSerialization,
              element,
              elementTypeRepr,
              index.toString()
            )
          )
          .reduce((prev, curr) => [prev, ", ", curr])}
        ]
      </Typography>
    );
  }

  if (summaryIsComplete && !summaryIsEmpty) return summary;

  return (
    <Table>
      <TableBody>
        <TableRow>
          <TableCell>
            <b>Total elements</b>
          </TableCell>
          <TableCell>{props.valueSummary["length"]}</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>
            <b>Excerpt</b>
          </TableCell>
          <TableCell>
            {summary} and{" "}
            {props.valueSummary["length"] -
              props.valueSummary["summary"].length}{" "}
            more items.
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
}

function TupleValueView(props: ValueViewProps) {
  let typeRepr = props.typeRepr as AliasTypeRepr;

  let elementTypesRepr = typeRepr[2].args;

  return (
    <List>
      {Array.from(props.valueSummary).map((element, index) => (
        <ListItem key={index}>
          {renderSummary(
            props.typeSerialization,
            element,
            elementTypesRepr[index].type as TypeRepr,
            index.toString()
          )}
        </ListItem>
      ))}
    </List>
  );
}

function ListTypeView(props: TypeViewProps) {
  let typeRepr = props.typeRepr as AliasTypeRepr;
  let typeArgs = typeRepr[2].args;

  if (typeArgs === undefined) {
    throw Error("Incorrect type serialization for " + typeRepr[1]);
  }

  let elementTypeRepr: TypeRepr = typeArgs[0].type as TypeRepr;

  return (
    <code>
      {"list["}
      {renderType(elementTypeRepr)}
      {"]"}
    </code>
  );
}

function UnionTypeView(props: TypeViewProps) {
  let typeRepr = props.typeRepr as AliasTypeRepr;
  let typeArgs = typeRepr[2].args;

  if (typeArgs === undefined) {
    throw Error("Incorrect type serialization for " + typeRepr[1]);
  }

  let unionTypeReprs: TypeRepr[] = typeArgs.map(
    (typeArg) => typeArg.type as TypeRepr
  );
  let key = 0;
  return (
    <code>
      <div>{"Union["}</div>
      {unionTypeReprs.map<React.ReactNode>((unionTypeRepr) => (
        <Box paddingLeft={5} key={key++}>
          {renderType(unionTypeRepr)}
          {", "}
        </Box>
      ))}
      <div>{"]"}</div>
    </code>
  );
}

function FloatInRangeTypeView(props: TypeViewProps) {
  let typeRepr = props.typeRepr as GenericTypeRepr;
  let typeParameters = typeRepr[2].parameters as Array<
    [string, ValueParamRepr]
  >;

  if (typeParameters === undefined) {
    return <Alert severity="error">Incorrect type serialization</Alert>;
  }

  return (
    <code>
      {"FloatInRange["}
      <Tooltip title="Lower bound">
        <span>{typeParameters[0][1].value}</span>
      </Tooltip>
      ,&nbsp;
      <Tooltip title="Upper bound">
        <span>{typeParameters[1][1].value}</span>
      </Tooltip>
      ,&nbsp;
      <Tooltip title="Lower inclusive">
        <span>{typeParameters[2][1].value ? "True" : "False"}</span>
      </Tooltip>
      ,&nbsp;
      <Tooltip title="Upper inclusive">
        <span>{typeParameters[3][1].value ? "True" : "False"}</span>
      </Tooltip>
      {"]"}
    </code>
  );
}

function DataclassTypeView(props: TypeViewProps) {
  let typeRepr = props.typeRepr as DataclassTypeRepr;
  let typeFields = typeRepr[2].fields;

  if (typeFields === undefined) {
    return <Alert severity="error">Incorrect type serialization</Alert>;
  }

  return (
    <code>
      <div>@dataclass</div>
      <div>{typeRepr[1]}:</div>
      <Table>
        <TableBody>
          {Object.entries(typeFields).map<React.ReactNode>(
            ([name, fieldTypeRepr]) => (
              <TableRow key={name}>
                <TableCell
                  sx={{
                    padding: 0,
                    paddingLeft: 5,
                    border: 0,
                    color: "GrayText",
                    width: "1%",
                    verticalAlign: "top",
                  }}
                >
                  <code>{name}:&nbsp;</code>
                </TableCell>
                <TableCell sx={{ border: 0, padding: 0, color: "GrayText" }}>
                  <code>{renderType(fieldTypeRepr.type as TypeRepr)}</code>
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </code>
  );
}

function DataclassValueView(props: ValueViewProps) {
  let valueSummary: {
    values: { [name: string]: any };
    types: { [name: string]: TypeSerialization };
  } = props.valueSummary;

  let typeRepr = props.typeRepr as DataclassTypeRepr;
  let typeFields = typeRepr[2].fields;
  if (typeFields === undefined) {
    return <Alert severity="error">Incorrect type serialization</Alert>;
  }

  return (
    <Stack>
      {Object.entries(valueSummary.values).map<React.ReactNode>(
        ([name, fieldSummary]) => (
          <Box
            key={name}
            sx={{ borderBottom: 1, borderColor: "#f0f0f0", py: 5 }}
          >
            <Typography variant="h6">{name}</Typography>
            <Box sx={{ mt: 3, pl: 5 }}>
              {renderSummary(
                valueSummary.types[name] || props.typeSerialization,
                fieldSummary,
                valueSummary.types[name]?.type || typeFields[name].type
              )}
            </Box>
          </Box>
        )
      )}
    </Stack>
  );
}

function DictValueView(props: ValueViewProps) {
  let typeRepr = props.typeRepr as AliasTypeRepr;

  let keyTypeRepr = typeRepr[2].args[0].type as TypeRepr;
  let valueTypeRepr = typeRepr[2].args[1].type as TypeRepr;

  let valueSummary = props.valueSummary as [any, any];

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>key</TableCell>
          <TableCell>value</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {Array.from(valueSummary).map((pair, index) => (
          <TableRow key={index}>
            <TableCell>
              {renderSummary(props.typeSerialization, pair[0], keyTypeRepr)}
            </TableCell>
            <TableCell>
              {renderSummary(props.typeSerialization, pair[1], valueTypeRepr)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function TorchDataLoaderValueView(props: ValueViewProps) {
  let { valueSummary } = props;

  return (
    <Table>
      <TableBody>
        <TableRow key="batch-size">
          <TableCell>
            <b>Batch size</b>
          </TableCell>
          <TableCell>{valueSummary["batch_size"]}</TableCell>
        </TableRow>
        <TableRow key="num_workers">
          <TableCell>
            <b>Number of suprocesses</b>
          </TableCell>
          <TableCell>{valueSummary["num_workers"]}</TableCell>
        </TableRow>
        <TableRow key="pin_memory">
          <TableCell>
            <b>Copy tensors into pinned memory</b>
          </TableCell>
          <TableCell>
            <BoolValueView
              {...props}
              valueSummary={valueSummary["pin_memory"]}
            />
          </TableCell>
        </TableRow>
        <TableRow key="timeout">
          <TableCell>
            <b>Timeout</b>
          </TableCell>
          <TableCell>{valueSummary["timeout"]} sec.</TableCell>
        </TableRow>
        <TableRow key="dataset">
          <TableCell>
            <b>Dataset</b>
          </TableCell>
          <TableCell>
            <ReprValueView {...props} valueSummary={valueSummary["dataset"]} />
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
}

function PlotlyFigureValueView(props: ValueViewProps) {
  let { valueSummary } = props;
  let { data, layout, config } = valueSummary["figure"];
  return <Plot data={data} layout={layout} config={config} />;
}

function MatplotlibFigureValueView(props: ValueViewProps) {
  let { valueSummary } = props;

  const hasFigureJsonData = useMemo(() => !!valueSummary['mpld3'], [valueSummary]);
  
  return hasFigureJsonData ? 
    <MatplotlibFigureValueFigure key={valueSummary['mpld3']['id']} spec={valueSummary['mpld3']} />
    : <MatplotlibFigureValueImage path={valueSummary['path']} /> ;
}

interface MatplotlibFigureValueImageProps{
  path: string
}

function MatplotlibFigureValueImage(props: MatplotlibFigureValueImageProps) {
  const { path } = props;
  return (
    <Zoom>
      <img src={path} width={"100%"} alt="matplotlib figure" />
    </Zoom>
  );
}

interface MatplotlibFigureValueFigureProps{
  spec: any
}

function MatplotlibFigureValueFigure(props: MatplotlibFigureValueFigureProps) {
  const { spec: specProp } = props;
  const figureId = useMemo(() => `fig-${uuidv4()}`, []);

  const drawFigure = useMatplotLib(figureId);

  const [figDivRef, { width, height}] = useMeasure<HTMLDivElement>();

  const hasFigureRendered = useRef(false)

  const [scaleAndTranslate, setScaleAndTranslate] = useState({
    scale: 1, translate: {x: 0, y: 0}
  });

  const [scaledHeight, setScaleHeight] = useState(0);

  useLayoutEffect(() => {
    // wait for the element's final layout when its width is fully expanded.
    if (!hasFigureRendered.current && width > 0) {
      const spec = {
        ...specProp,
        plugins: []
      };

      const scaledHeight = width / spec.width * spec.height;
      
      drawFigure(spec);

      const scale = width / spec.width;

      setScaleHeight(scaledHeight);
      setScaleAndTranslate({
        scale: scale,
        translate: {
          x: (width - spec.width) / 2,
          y: (scaledHeight - spec.height) / 2
        }
      })

      hasFigureRendered.current = true;
    }
  }, [width, height, drawFigure, figureId, specProp]);

  return <div ref={figDivRef} style={{width: "100%", height: `${scaledHeight}px`}} >
      <div id={figureId} style={{width: "100%", height: '100%',
      transform: `scale(${scaleAndTranslate.scale})` + 
      ` translate(${scaleAndTranslate.translate.x}px, ${scaleAndTranslate.translate.y}px)`}}/>
    </div>
}

function DataFrameTable(props: {
  dataframe: { [k: string]: { [v: string]: any } };
  dtypes: [string, string][];
  index: any[];
}) {
  let { dataframe, dtypes, index } = props;

  let indexColumn: { [v: string]: any } = {};
  index.forEach((i) => (indexColumn[i] = i));
  dataframe = { index: indexColumn, ...dataframe };

  dtypes = [["index", "index"], ...dtypes];

  let length = 0;
  const entries = Object.entries(dataframe);
  if (entries.length > 0) {
    length = Object.entries(entries[0][1]).length;
  }

  const orderedCols: string[] = useMemo(
    () => dtypes.map((value) => value[0]),
    [dtypes]
  );

  const columns: GridColumn[] = useMemo(
    () => dtypes.map((value) => ({ id: value[0], title: value[0] })),
    [dtypes]
  );

  const dtypesByColumn: Map<string, string> = useMemo(
    () => new Map(dtypes),
    [dtypes]
  );

  const getContent = React.useCallback((cell: Item): GridCell => {
    const [col, row] = cell;

    const column = orderedCols[col];
    const dataRow = dataframe[column];

    let data = dataRow[index[row]];
    let displayData = "";
    try {
      displayData = data.toString();
    } catch {}

    let kind: GridCellKind = GridCellKind.Text;
    let dtype = dtypesByColumn.get(column);

    if (dtype?.startsWith("int") || dtype?.startsWith("float")) {
      kind = GridCellKind.Number;
      data = data === null ? undefined : data;
      displayData = data === null ? "null" : displayData;
    } else if (dtype === "bool") {
      kind = GridCellKind.Boolean;
    } else if (dtype === "index") {
      kind = GridCellKind.RowID;
      data = data.toString();
    }
    return {
      kind: kind,
      allowOverlay: false,
      displayData: displayData,
      data: data,
    };
  }, [dataframe, dtypesByColumn, index, orderedCols]);

  return (
    <DataEditor getCellContent={getContent} columns={columns} rows={length} />
  );
}

function DataFrameValueView(props: ValueViewProps) {
  let { valueSummary } = props;
  let { dataframe, describe, truncated, shape, index } = valueSummary;
  let dtypes: [string, string][] = valueSummary["dtypes"];

  let describeDtypes: [string, string][] = Object.entries(describe).map(
    (field) => [field[0], "float64"]
  );

  const describeIndex = [
    "count",
    "mean",
    "std",
    "min",
    "25%",
    "50%",
    "75%",
    "max",
  ];

  return (
    <>
      <Box marginTop={5}>
        <Typography variant="h6">Dataframe shape</Typography>
        <Box marginTop={5}>
          <Typography>
            {shape[0]} rows &times; {shape[1]} columns
          </Typography>
        </Box>
      </Box>
      <Box marginTop={10}>
        <Typography variant="h6">
          Dataframe {truncated ? "preview" : ""}
        </Typography>
        <Box marginTop={5}>
          <DataFrameTable dataframe={dataframe} dtypes={dtypes} index={index} />
          {truncated && (
            <Typography>... and {shape[0] - 5} rows not shown.</Typography>
          )}
        </Box>
      </Box>
      <Box marginTop={10}>
        <Typography variant="h6">Describe</Typography>
        <Box marginTop={5}>
          <DataFrameTable
            dataframe={describe}
            dtypes={describeDtypes}
            index={describeIndex}
          />
        </Box>
      </Box>
    </>
  );
}

function LinkValueView(props: ValueViewProps) {
  let { valueSummary } = props;
  let { values } = valueSummary;

  return (
    <Button
      href={values.url}
      variant="contained"
      target="blank"
      endIcon={<OpenInNew />}
    >
      {values.label}
    </Button>
  );
}

function DatetimeValueView(props: ValueViewProps) {
  const { valueSummary } = props;
  const date = parseISO(valueSummary);

  if (!valueSummary || !isValid(date)) {
    return <Alert severity="error">Incorrect date value.</Alert>;
  }
  return <Typography>{format(date, "LLLL d, yyyy h:mm:ss a xxx")}</Typography>;
}

function EnumValueView(props: ValueViewProps) {
  const { valueSummary } = props;
  return <Chip label={valueSummary} variant="outlined" />;
}

function S3LocationValueView(props: ValueViewProps) {
  const { valueSummary } = props;
  const { values } = valueSummary;

  const bucketSummary = values.bucket.values;

  return <S3Button region={bucketSummary.region} bucket={bucketSummary.name} location={values.location} />;
}

function S3BucketValueView(props: ValueViewProps) {
  const { valueSummary } = props;
  const { values } = valueSummary;

  return <S3Button region={values.region} bucket={values.name} />
}

function S3Button(props: {region?: string, bucket: string, location?: string}) {
  const { region, bucket, location } = props;

  let s3URI = "s3://" + bucket;
  let href = new URL("https://s3.console.aws.amazon.com/s3/object/" + bucket);
  
  if (region !== null && region !== undefined) {
    href.searchParams.append("region", region);
  }

  if (location !== undefined) {
    s3URI = s3URI + "/" + location;
    href.searchParams.append("prefix", location);
  }

  return <>
  <Tooltip title="View in AWS console">
    <Button
      href={href.href}
      variant="outlined"
      target="blank"
      endIcon={<OpenInNew />}
    >
      <img src={S3Icon} width="20px" style={{paddingRight: "5px"}} alt="S3 icon"/>
      {s3URI}
    </Button>
    </Tooltip>
  </>;
}

function ImageValueView(props: ValueViewProps) {
  const { valueSummary } = props;
  const { bytes } = valueSummary;

  return <img
    src={`/api/v1/storage/blobs/${bytes.blob}/data`}
    alt="Artifact rendering"
    style={{maxWidth: "600px"}}
  />
}

type ComponentPair = {
  type: (props: TypeViewProps) => JSX.Element;
  value: (props: ValueViewProps) => JSX.Element;
};

const TypeComponents: Map<string, ComponentPair> = new Map([
  ["NoneType", { type: TypeView, value: NoneValueView }],
  ["float", { type: TypeView, value: FloatValueView }],
  ["str", { type: TypeView, value: StrValueView }],
  ["int", { type: TypeView, value: IntValueView }],
  ["bool", { type: TypeView, value: BoolValueView }],
  ["FloatInRange", { type: FloatInRangeTypeView, value: FloatValueView }],
  ["list", { type: ListTypeView, value: ListValueView }],
  ["tuple", { type: TypeView, value: TupleValueView }],
  ["dict", { type: TypeView, value: DictValueView }],
  ["dataclass", { type: DataclassTypeView, value: DataclassValueView }],
  ["Union", { type: UnionTypeView, value: ValueView }],
  ["Link", { type: TypeView, value: LinkValueView }],
  ["datetime.datetime", { type: TypeView, value: DatetimeValueView }],
  ["enum.Enum", { type: TypeView, value: EnumValueView }],
>>>>>>> 9beb5c5 (PR comments)
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
  [
    "sematic.types.types.aws.s3.S3Bucket",
    {
      value: S3BucketValueView,
    }
  ],
  [
    "sematic.types.types.aws.s3.S3Location",
    {
      value: S3LocationValueView,
    }
  ],
  [
    "sematic.types.types.image.Image",
    {
      value: ImageValueView,
    }
  ]
];


meta.forEach(([key, value]) => {
  TypeComponents.set(key, value);
});

