import styled from "@emotion/styled";
import { ColumnHelper } from "@tanstack/react-table";
import { parseJSON } from "date-fns";
import { Run } from "src/Models";
import { DateTimeLongConcise } from "src/component/DateTime";
import NameTag from "src/component/NameTag";
import { RunReference } from "src/component/RunReference";
import RunStatusColumn from "src/pages/RunSearch/RunStatusColumn";
import NameColumn from "src/pages/RunTableCommon/NameColumn";
import TagsColumn from "src/pages/RunTableCommon/TagsColumn";
import theme from "src/theme/new";


const StyledRunReferenceLink = styled(RunReference)`
    color: ${theme.palette.mediumGrey.main};
`;

export const IdColumnDef = (columnHelper: ColumnHelper<Run>) =>
    columnHelper.accessor("id", {
        meta: {
            columnStyles: {
                width: "5.923%", // this is the remainder value of 1 substracting the percentage of all other columns
            }
        },
        header: "ID",
        cell: info => <StyledRunReferenceLink runId={info.getValue()} />,
    });

export const SubmissionTimeColumnDef = (columnHelper: ColumnHelper<Run>) =>
    columnHelper.accessor("created_at", {
        meta: {
            columnStyles: {
                width: "12.3396%", // this is the minWidth(150px) divided by the sum of the minWidths of all other columns.
                minWidth: "150px"
            }
        },
        header: "Submitted at",
        cell: info => DateTimeLongConcise(parseJSON(info.getValue())),
    });

export const NameColumnDef = (columnHelper: ColumnHelper<Run>) =>
    columnHelper.accessor(run => [run.name, run.function_path], {
        meta: {
            columnStyles: {
                width: "1px",
                maxWidth: "calc(100vw - 1100px)"
            }
        },
        header: "Name",
        cell: info => {
            const [name, importPath] = info.getValue();
            return <NameColumn name={name} importPath={importPath} />
        },
    });

export const TagsColumnDef = (columnHelper: ColumnHelper<Run>) =>
    columnHelper.accessor("tags", {
        meta: {
            columnStyles: {
                width: "14.5114%", // this is the minWidth(160px) divided by the sum of the minWidths of all other columns.
                minWidth: "160px"
            }
        },
        header: "Tags",
        cell: info => <TagsColumn tags={info.getValue()} />,
    });

export const OwnerColumnDef = (columnHelper: ColumnHelper<Run>) =>
    columnHelper.accessor(data => ({
        firstName: data.user?.first_name,
        lastName: data.user?.last_name
    }), {
        meta: {
            columnStyles: {
                width: "8.39092%", // this is the minWidth (100px) divided by the sum of the minWidths of all other columns.
                maxWidth: "max(100px, 8.39092%)",
            }
        },
        header: "Owner",
        cell: info => <NameTag {...info.getValue()} />,
    });

export const StatusColumnDef = (columnHelper: ColumnHelper<Run>) =>
    columnHelper.accessor(data => ({
        futureState: data.future_state,
        createdAt: data.created_at,
        failedAt: data.failed_at,
        resolvedAt: data.resolved_at
    }), {
        meta: {
            columnStyles: {
                width: "15.7947%", // this is the minWidth (200px) divided by the sum of the minWidths of all other columns.
                minWidth: "200px"
            }
        },
        header: "Status",
        cell: info => <RunStatusColumn {...info.getValue() as any} />,
    });
