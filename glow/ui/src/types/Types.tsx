import Typography from "@mui/material/Typography";
import React from "react";

export type TypeRepr = [
  string | undefined,
  string,
  { [k: string]: any } | undefined
];

export type TypeRegistry = Map<string, Array<TypeRepr>>;

export type TypeSerialization = {
  type: TypeRepr;
  registry: TypeRegistry;
};

interface ValueViewProps {
  typeRepr: TypeRepr;
  typeSerialization: TypeSerialization;
  valueSummary: any;
}

function ValueView(props: ValueViewProps) {
  return <code>{JSON.stringify(props.valueSummary)}</code>;
}

function FloatView(props: ValueViewProps) {
  return (
    <Typography display="inline" component="span">
      {Number.parseFloat(props.valueSummary).toFixed(1)}
    </Typography>
  );
}

function ListView(props: ValueViewProps) {
  let typeRepr = props.typeSerialization.type[2];
  if (typeRepr === undefined) {
    throw Error("Incorrect type serialization");
  }
  let elementTypeRepr: TypeRepr = typeRepr["args"][0]["type"];
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

interface TypeViewProps {
  typeRepr: TypeRepr;
}

function TypeView(props: TypeViewProps) {
  return (
    <code>
      {props.typeRepr[1]}
      {props.typeRepr[2] && "[" + JSON.stringify(props.typeRepr[2]) + "]"}
    </code>
  );
}

function ListTypeView(props: TypeViewProps) {
  let typeArgs = props.typeRepr[2];
  if (typeArgs === undefined) {
    throw Error("Incorrect type serialization");
  }
  let elementTypeRepr: TypeRepr = typeArgs["args"][0]["type"];

  return (
    <code>
      {"list["}
      {renderType(elementTypeRepr)}
      {"]"}
    </code>
  );
}

function FloatInRangeTypeView(props: TypeViewProps) {
  let typeArgs = props.typeRepr[2];
  if (typeArgs === undefined) {
    throw Error("Incorrect type serialization");
  }
  let params = typeArgs["parameters"];
  return (
    <code>
      {"FloatInRange["}
      {params["lower_bound"]["value"]},&nbsp;
      {params["upper_bound"]["value"]},&nbsp;
      {params["lower_inclusive"]["value"] ? "True" : "False"},&nbsp;
      {params["upper_inclusive"]["value"] ? "True" : "False"}
      {"]"}
    </code>
  );
}

export function renderSummary(
  typeSerialization: TypeSerialization,
  valueSummary: any,
  typeRepr?: TypeRepr,
  key?: string
): JSX.Element {
  typeRepr = typeRepr || typeSerialization.type;
  let components = TypeComponents.get(typeRepr[1]);
  if (components) {
    let ValueViewComponent = components.value;
    return (
      <ValueViewComponent
        key={key}
        typeRepr={typeRepr}
        typeSerialization={typeSerialization}
        valueSummary={valueSummary}
      />
    );
  }

  let parentType = new Map<string, any>(
    Object.entries(typeSerialization.registry)
  ).get(typeRepr[1]);
  if (parentType) {
    return renderSummary(typeSerialization, valueSummary, parentType[0], key);
  }

  return (
    <ValueView
      typeRepr={typeRepr}
      typeSerialization={typeSerialization}
      valueSummary={valueSummary}
    />
  );
}

export function renderType(typeRepr: TypeRepr): JSX.Element {
  let components = TypeComponents.get(typeRepr[1]);
  if (components) {
    let TypeViewComponent = components.type;
    return <TypeViewComponent typeRepr={typeRepr} />;
  }

  return <TypeView typeRepr={typeRepr} />;
}

const TypeComponents: Map<
  string,
  {
    type: (props: TypeViewProps) => JSX.Element;
    value: (props: ValueViewProps) => JSX.Element;
  }
> = new Map([
  ["float", { type: TypeView, value: FloatView }],
  ["FloatInRange", { type: FloatInRangeTypeView, value: FloatView }],
  ["list", { type: ListTypeView, value: ListView }],
]);
