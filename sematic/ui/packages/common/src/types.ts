type TypeCategory = "builtin" | "typing" | "dataclass" | "generic" | "class";

export type BaseTypeRepr = [TypeCategory, string, { [k: string]: any }];

export type TypeParamRepr = { type: BaseTypeRepr };

export type AliasTypeRepr = ["typing", string, { args: Array<TypeParamRepr> }];

export type TypeRegistry = Map<string, Array<AnyTypeRepr>>;

export type SpecificTypeSerialization<TRepr> = {
  type: TRepr;
  registry: TypeRegistry;
};

// TypeRepr types
export type AnyTypeRepr =
  BaseTypeRepr
  | AliasTypeRepr
  | DataclassTypeRepr

type GenerateTypeSerializationType<U> = U extends AnyTypeRepr ? SpecificTypeSerialization<U> : never; 
export type AnyTypeSerialization = GenerateTypeSerializationType<AnyTypeRepr>;

// Specific Types
// Defined here due to circular dependency
export type DataclassTypeRepr = [
    "dataclass",
    string,
    { import_path: string; fields: { [name: string]: TypeParamRepr } }
];
