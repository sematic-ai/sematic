import DataEditor, {
    GridCell,
    GridCellKind,
    GridColumn,
    Item,
} from "@glideapps/glide-data-grid";
import { useCallback, useMemo } from "react";
import { ArtifactExpanderContainer, ArtifactLine } from "src/typeViz/ArtifactVizTemplate";
import { ValueComponentProps, ViewComponentProps, renderArtifactRow } from "src/typeViz/common";

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

    const getContent = useCallback((cell: Item): GridCell => {
        const [col, row] = cell;

        const column = orderedCols[col];
        const dataRow = dataframe[column];

        let data = dataRow[index[row]];
        let displayData = "";
        try {
            displayData = data.toString();
        } catch { }

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

export default function DataFrameValueView(props: ValueComponentProps) {
    const { open } = props;
    return open ? null : (<span>Expand details</span>)
}

export function DataFrameDetailsView(props: ViewComponentProps) {
    let { valueSummary, typeSerialization } = props;
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

    return <>
        <ArtifactLine name={"Dataframe shape"}>
            {shape[0]} rows &times; {shape[1]} columns
        </ArtifactLine>
        {renderArtifactRow("Dataframe preview", {
            type: ["builtin", "DataFrameDataPreview", {}],
            registry: typeSerialization.registry
        }, {
            dataframe,
            dtypes,
            index,
            truncated,
            remainingRows: shape[0] - 5
        })}
        {renderArtifactRow("Describe", {
            type: ["builtin", "DataFrameDataDescribe", {}],
            registry: typeSerialization.registry
        }, {
            dataframe: describe,
            dtypes: describeDtypes,
            index: describeIndex,
            truncated: false
        })}
    </>
}

export function DataFrameSummaryView(props: ValueComponentProps) {
    const { open } = props;
    return open ? null : (<span>Click to see data</span>)
}

export function DataFrameSummaryExpandedView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { dataframe, dtypes, index, truncated, remainingRows } = valueSummary;

    const infoSection = useMemo(() => {
        if (!truncated) return null;
        return `... and ${remainingRows} more row${remainingRows === 1 ?  "" : "s"} not shown.`;
    }, [truncated, remainingRows])
    
    return <>
        <ArtifactExpanderContainer>
            <div style={{ overflowX: "auto" }}>
                <DataFrameTable dataframe={dataframe} dtypes={dtypes} index={index} />
                {infoSection}
            </div>
        </ArtifactExpanderContainer>
    </>;
}
