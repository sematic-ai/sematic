import Typography from "@mui/material/Typography";
import React from "react";
import Tooltip from "@mui/material/Tooltip";
import Alert from "@mui/material/Alert";
import Table from "@mui/material/Table";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import TableBody from "@mui/material/TableBody";

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
  return (
    <code>
      {repr[1]}
      {Object.keys(repr[2]).length > 0 && "[" + JSON.stringify(repr[2]) + "]"}
    </code>
  );
}

export function renderType(typeRepr: TypeRepr): JSX.Element {
  let typeKey = typeRepr[1];
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

  return (
    <ValueView
      typeRepr={typeRepr}
      typeSerialization={typeSerialization}
      valueSummary={valueSummary}
    />
  );
}

function FloatView(props: ValueViewProps) {
  return (
    <Typography display="inline" component="span">
      {Number.parseFloat(props.valueSummary).toFixed(1)}
    </Typography>
  );
}

function ListView(props: ValueViewProps) {
  let typeRepr = props.typeRepr as AliasTypeRepr;
  if (!typeRepr[2].args) {
    return <Alert severity="error">Incorrect type serialization</Alert>;
  }

  let elementTypeRepr: TypeRepr = typeRepr[2].args[0].type as TypeRepr;

  return (
    <Typography display="inline" component="span">
      [
      {Object.entries(props.valueSummary)
        .map<React.ReactNode>((pairs) =>
          renderSummary(
            props.typeSerialization,
            pairs[1],
            elementTypeRepr,
            pairs[0]
          )
        )
        .reduce((prev, curr) => [prev, ", ", curr])}
      ]
    </Typography>
  );
}

function ListTypeView(props: TypeViewProps) {
  let typeRepr = props.typeRepr as AliasTypeRepr;
  let typeArgs = typeRepr[2].args;

  if (typeArgs === undefined) {
    return <Alert severity="error">Incorrect type serialization</Alert>;
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
    <Table>
      <TableBody>
        {Object.entries(valueSummary.values).map<React.ReactNode>(
          ([name, fieldSummary]) => (
            <TableRow key={name}>
              <TableCell sx={{ verticalAlign: "top" }}>
                <b>{name}</b>
              </TableCell>
              <TableCell>
                {renderSummary(
                  valueSummary.types[name] || props.typeSerialization,
                  fieldSummary,
                  valueSummary.types[name]?.type || typeFields[name].type
                )}
              </TableCell>
            </TableRow>
          )
        )}
      </TableBody>
    </Table>
  );
}

type ComponentPair = {
  type: (props: TypeViewProps) => JSX.Element;
  value: (props: ValueViewProps) => JSX.Element;
};

const TypeComponents: Map<string, ComponentPair> = new Map([
  ["float", { type: TypeView, value: FloatView }],
  ["FloatInRange", { type: FloatInRangeTypeView, value: FloatView }],
  ["list", { type: ListTypeView, value: ListView }],
  ["dataclass", { type: DataclassTypeView, value: DataclassValueView }],
]);

function getComponentPair(typeRepr: TypeRepr) {
  let typeKey = typeRepr[1];
  let componentPair = TypeComponents.get(typeKey);

  if (typeRepr[0] === "dataclass" && !componentPair) {
    componentPair = TypeComponents.get("dataclass");
  }
  return componentPair;
}
