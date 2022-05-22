export type TypeRepr = [
  string | undefined,
  string,
  Map<string, any> | undefined
];

export type TypeRegistry = Map<string, Array<TypeRepr>>;

export type TypeSerialization = {
  type: TypeRepr;
  registry: TypeRegistry;
};

interface ValueViewProps {
  typeSerialization: TypeSerialization;
  valueSummary: any;
}

export function ValueView(props: ValueViewProps) {
  return <code>{JSON.stringify(props.valueSummary)}</code>;
}

export function FloatView(props: ValueViewProps) {
  return <span>{Number.parseFloat(props.valueSummary).toFixed(2)}</span>;
}

interface TypeViewProps {
  typeSerialization: TypeSerialization;
}

export function TypeView(props: TypeViewProps) {
  return (
    <code>
      {props.typeSerialization.type[1]}
      {props.typeSerialization.type[2] &&
        "(" + JSON.stringify(props.typeSerialization.type[2]) + ")"}
    </code>
  );
}

export function renderSummary(
  typeSerialization: TypeSerialization,
  valueSummary: any
): JSX.Element {
  let components = TypeComponents.get(typeSerialization.type[1]);
  if (components) {
    let ValueViewComponent = components.value;
    return (
      <ValueViewComponent
        typeSerialization={typeSerialization}
        valueSummary={valueSummary}
      />
    );
  }
  return (
    <ValueView
      typeSerialization={typeSerialization}
      valueSummary={valueSummary}
    />
  );
}

export function renderType(typeSerialization: TypeSerialization): JSX.Element {
  let components = TypeComponents.get(typeSerialization.type[1]);
  if (components) {
    let TypeViewComponent = components.type;
    return <TypeViewComponent typeSerialization={typeSerialization} />;
  }

  return <TypeView typeSerialization={typeSerialization} />;
}

const TypeComponents: Map<
  string,
  {
    type: (props: TypeViewProps) => JSX.Element;
    value: (props: ValueViewProps) => JSX.Element;
  }
> = new Map([["float", { type: TypeView, value: FloatView }]]);
