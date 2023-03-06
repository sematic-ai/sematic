
import React from 'react';
import type { ComponentRenderDetails, AnyTypeRepr } from './Types';
export type { AnyTypeRepr, AnyTypeSerialization } from './Types';

// Defs (compile time)

export type TypeRegistry = Map<string, Array<AnyTypeRepr>>;

export type SpecificTypeSerialization<TRepr> = {
  type: TRepr;
  registry: TypeRegistry;
};

export interface ValueViewProps<TRepr> {
  typeRepr: TRepr;
  typeSerialization: SpecificTypeSerialization<TRepr>;
  valueSummary: any;
  key?: string;
}

export interface CommonValueViewProps {
  valueSummary: any;
}

export type AliasValueViewProps = ValueViewProps<AliasTypeRepr>;

type TypeCategory = "builtin" | "typing" | "dataclass" | "generic" | "class";

export type BaseTypeRepr = [TypeCategory, string, { [k: string]: any }];

export type TypeParamRepr = { type: BaseTypeRepr };

export type AliasTypeRepr = ["typing", string, { args: Array<TypeParamRepr> }];


// Implementation (runtime)

export function ValueView(props: CommonValueViewProps) {
  return <code>{JSON.stringify(props.valueSummary)}</code>;
}

export function ReprValueView(props: CommonValueViewProps) {
  return <pre>{props.valueSummary["repr"]}</pre>;
}

// Define here, but fill data in `Types.tsx` (avoid circular dependency)
export const TypeComponents: Map<string, ComponentRenderDetails> = new Map(
);

export function renderSummary<TypeRepr extends AnyTypeRepr>(
  typeSerialization: SpecificTypeSerialization<TypeRepr>,
  valueSummary: any,
  typeRepr?: TypeRepr,
  key?: string
): JSX.Element {
  typeRepr = typeRepr || typeSerialization.type;

  let typeKey = typeRepr[1];
  let componentRenderDetails = getComponentRenderDetails(typeRepr);

  if (componentRenderDetails) {
    let ValueViewComponent = componentRenderDetails.value;
    return (
      React.createElement(ValueViewComponent as any, {
        typeRepr, typeSerialization, valueSummary, key
      })
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
      <ReprValueView valueSummary={valueSummary} key={key} />
    );
  }

  return (
    <ValueView valueSummary={valueSummary} key={key} />
  );
}

function getComponentRenderDetails(typeRepr: AnyTypeRepr) {
  let typeKey = typeRepr[1];
  if (typeRepr[0] === "class") {
    typeKey = typeRepr[2]["import_path"] + "." + typeKey;
  }

  let componentRenderDetails = TypeComponents.get(typeKey);

  if (typeRepr[0] === "dataclass" && !componentRenderDetails) {
    componentRenderDetails = TypeComponents.get("dataclass");
  }
  return componentRenderDetails;
}

