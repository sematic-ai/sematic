import React, { useMemo } from "react";
import Plotly from "plotly.js-cartesian-dist";
import Zoom from "react-medium-image-zoom";
import "react-medium-image-zoom/dist/styles.css";
import DataEditor, {
  Item,
  GridCell,
  GridColumn,
  GridCellKind,
} from "@glideapps/glide-data-grid";

import createPlotlyComponent from "react-plotly.js/factory";
import {
  Stack,
  Typography,
  Tooltip,
  Box,
  Alert,
  Table,
  TableCell,
  TableRow,
  TableBody,
  Chip,
  List,
  ListItem,
  TableHead,
  Button,
} from "@mui/material";
import { OpenInNew } from "@mui/icons-material";
import {format, isValid, parseISO} from "date-fns";

const Plot = createPlotlyComponent(Plotly);

type TypeCategory = "builtin" | "typing" | "dataclass" | "generic" | "class";

type BaseTypeRepr = [TypeCategory, string, { [k: string]: any }];

type TypeParamRepr = { type: BaseTypeRepr };

type AliasTypeRepr = ["typing", string, { args: Array<TypeParamRepr> }];

type BuiltinTypeRepr = ["builtin", string, {}];

type DataclassTypeRepr = [
  "dataclass",
  string,
  { import_path: string; fields: { [name: string]: TypeParamRepr } }
];

type ValueParamRepr = { value: string | number | boolean | null };
type GenericTypeRepr = [
  "generic",
  string,
  {
    parameters: Array<[string, TypeParamRepr | ValueParamRepr]>;
  }
];

type ClassTypeRepr = ["class", string, { import_path: string }];

type TypeRepr =
  | AliasTypeRepr
  | BuiltinTypeRepr
  | DataclassTypeRepr
  | GenericTypeRepr
  | ClassTypeRepr;

type TypeRegistry = Map<string, Array<TypeRepr>>;

export type TypeSerialization = {
  type: TypeRepr;
  registry: TypeRegistry;
};

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
            {props.valueSummary["length"] - props.valueSummary["summary"].length}{" "}
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
  let { path } = valueSummary;
  return (
    <Zoom>
      <img src={path} width={"100%"} alt="matplotlib figure" />
    </Zoom>
  );
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
  }, []);

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
  const {valueSummary} = props;
  const date = parseISO(valueSummary)

  if (!valueSummary || !isValid(date)) {
      return <Alert severity="error">Incorrect date value.</Alert>;
  }
  return (
      <Typography>{format(date, "LLLL d, yyyy h:mm:ss a xxx", )}</Typography>
  );
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
  ["datetime.datetime", {type: TypeView, value: DatetimeValueView}],
  [
    "torch.utils.data.dataloader.DataLoader",
    { type: TypeView, value: TorchDataLoaderValueView },
  ],
  [
    "plotly.graph_objs._figure.Figure",
    { type: TypeView, value: PlotlyFigureValueView },
  ],
  [
    "matplotlib.figure.Figure",
    { type: TypeView, value: MatplotlibFigureValueView },
  ],
  [
    "pandas.core.frame.DataFrame",
    {
      type: TypeView,
      value: DataFrameValueView,
    },
  ],
]);

function getComponentPair(typeRepr: TypeRepr) {
  let typeKey = typeRepr[1];
  if (typeRepr[0] === "class") {
    typeKey = typeRepr[2]["import_path"] + "." + typeKey;
  }

  let componentPair = TypeComponents.get(typeKey);

  if (typeRepr[0] === "dataclass" && !componentPair) {
    componentPair = TypeComponents.get("dataclass");
  }
  return componentPair;
}
