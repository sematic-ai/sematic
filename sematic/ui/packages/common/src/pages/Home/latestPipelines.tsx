import styled from "@emotion/styled";
import { Table, createColumnHelper, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { useMemo } from "react";
import { Run } from "src/Models";
import MuiRouterLink from "src/component/MuiRouterLink";
import { useFetchRuns } from "src/hooks/runHooks";
import StateChipColumnDef from "src/pages/Home/RunStateChipColumn";
import { LastActiveTimeColumnDef, RowAutoAdaptTable } from "src/pages/Home/common";
import { NameColumnDef } from "src/pages/RunTableCommon/columnDefinition";
import theme from "src/theme/new";

const StyledSection = styled.section`
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    height: 50px;

    font-size: ${theme.typography.fontSize}px;
    font-weight: ${theme.typography.fontWeightBold};

    flex-grow: 0;
    flex-shrink: 0;
    
    a {
        margin-right: 0;
    }
`;

const columnHelper = createColumnHelper<Run>();

const columns =[
    StateChipColumnDef(columnHelper),
    NameColumnDef(columnHelper),
    LastActiveTimeColumnDef(columnHelper),
];

interface LatestRunsPresentationProps {
    runs: Run[];
}

function LatestRunsPresentation(props: LatestRunsPresentationProps) {
    const { runs } = props;

    const tableInstance = useReactTable({
        data: runs,
        columns,
        getCoreRowModel: getCoreRowModel()
    });

    return <RowAutoAdaptTable tableInstance={tableInstance as Table<unknown> } />;
}

const filter =  { parent_id: { eq: null } };
const query =  { group_by: "function_path", limit: "10" };


export default function LatestPipelines() {
    const { isLoaded, runs } = useFetchRuns(filter, query);

    return <>
        <StyledSection>
            <span>
                Your latest pipelines
            </span>
            <span>
                <MuiRouterLink variant="subtitle1" type="menu" href={"/pipelines"}>
                    See all
                </MuiRouterLink>
            </span>
        </StyledSection>
        {useMemo(() => {
            if (!isLoaded) {
                // TODO skeleton
                return <div>Loading...</div>
            }
            return <LatestRunsPresentation runs={runs} />;
        }, [runs, isLoaded])}
    </>
}