import ArtifactVizTemplate from "src/typeViz/ArtifactVizTemplate";
import { RenderDetails, TypeComponents } from "src/typeViz/vizMapping";
import { AnyTypeRepr, AnyTypeSerialization } from "src/types";

export interface ViewComponentProps {
    valueSummary: any;
    typeSerialization: AnyTypeSerialization;
}

export interface ValueComponentProps extends ViewComponentProps {
    open: boolean;
}

export type ValueComponentType = React.ComponentClass<ValueComponentProps> | React.FunctionComponent<ValueComponentProps>;
export type NestedViewComponentType = React.ComponentClass<ViewComponentProps> | React.FunctionComponent<ViewComponentProps>;

export function getTypeName(typeSerialization: AnyTypeSerialization) {
    const typeRepr = typeSerialization.type as AnyTypeRepr;

    if (!typeRepr?.[1]) {
        return "unknown";
    }

    // prefer the import path if it exists
    if ("import_path" in typeRepr[2]) {
        return typeRepr[2]["import_path"] + "." + typeRepr[1];
    }

    return typeRepr[1];
}

function getComponentRenderDetails(typeSerialization: AnyTypeSerialization): {
    renderDetails: RenderDetails,
    type: AnyTypeRepr
} | undefined {
    const typeRepr = typeSerialization.type as AnyTypeRepr;
    if (!typeRepr)  {
        return undefined;
    }
    let typeKey = typeRepr[1];

    // Prioritize on adopting the mapping with the full import path.
    // This makes it so we don't have to create a shadow dataclass
    // to have a custom viz for a particular dataclass. We can just
    // register the React component with the full import path of the dataclass.
    if ("import_path" in typeRepr[2]) {
        typeKey = typeRepr[2]["import_path"] + "." + typeKey;
    }

    let renderDetails = TypeComponents.get(typeKey);
    if (renderDetails) {
        return {
            renderDetails,
            type: typeRepr
        }
    }

    if (typeRepr[0] === "dataclass" && !renderDetails) {
        return {
            renderDetails: TypeComponents.get("dataclass")!,
            type: typeRepr
        }
    }

    if (!renderDetails) {
        // Try to find a parent type that has a registered component
        const registry = typeSerialization.registry as unknown as Record<string, AnyTypeRepr[]>;
        typeKey = typeRepr[1];
        const parentTypes = registry[typeKey];
        if (parentTypes && parentTypes.length > 0) {
            return getComponentRenderDetails({
                registry: typeSerialization.registry, type: parentTypes[0]
            });
        }
    }

    return undefined;
}

type renderArtifactRowOptions = {
    expanded?: boolean;
}

export function renderArtifactRow(name: string, typeSerialization: AnyTypeSerialization, valueSummary: any, 
    options = {} as renderArtifactRowOptions) {
    const { expanded = false } = options;
    let result = getComponentRenderDetails(typeSerialization);
    let type: AnyTypeRepr;
    let renderDetails: RenderDetails;

    if (result) {
        ({ type, renderDetails } = result);
    } else { // Fallback to repr or val
        ({ type } = typeSerialization);
        if (valueSummary["repr"] !== undefined) {
            renderDetails = TypeComponents.get("repr")!;
        } else {
            renderDetails = TypeComponents.get("val")!;
        }
    }

    return <ArtifactVizTemplate key={name} name={name} renderDetails={renderDetails}
        typeSerialization={{ registry: typeSerialization.registry, type }} valueSummary={valueSummary}
        defaultOpen={expanded} />
}
