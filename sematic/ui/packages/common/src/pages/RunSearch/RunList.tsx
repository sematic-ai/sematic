import styled from "@emotion/styled";
import { ChevronLeft, ChevronRight } from "@mui/icons-material";
import Typography from "@mui/material/Typography";
import { createColumnHelper, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { parseJSON } from "date-fns";
import { DateTimeLongConcise } from "src/component/DateTime";
import ImportPath from "src/component/ImportPath";
import PipelineTitle from "src/component/PipelineTitle";
import RunReferenceLink from "src/component/RunReferenceLink";
import TableComponent from "src/component/Table";
import TagsList from "src/component/TagsList";
import RunStatusColumn from "src/pages/RunSearch/RunStatusColumn";
import theme from "src/theme/new";

const Container = styled.div`
    display: flex;
    flex-direction: column;
    height: 100%;
    margin-right: -${theme.spacing(5)};
`;

const Stats = styled.div`
    height: 50px;
    width: 100%;
    display: flex;
    align-items: center;
    flex-grow: 0;
    flex-shrink: 0;
`;

const Pagination = styled.div`
    height: 50px;
    width: 100%;
    display: flex;
    align-items: center;
    flex-grow: 0;
    flex-shrink: 0;
    justify-content: flex-end;
    padding-right: ${theme.spacing(6)};

    svg {
        cursor: pointer;
    }
`;

const NameSection = styled.div`
    display: flex;
    flex-direction: row;
    column-gap: ${theme.spacing(2)};
    overflow-x: hidden;
    min-width: 100px;
    position: relative;
`;

const StyledRunReferenceLink = styled(RunReferenceLink)`
    color: ${theme.palette.mediumGrey.main};
`;

const RunData = {
    ID: '3es92wd',
    created: '2021-10-01T12:00:00Z',
    name: 'MNIST PyTorch Example',
    importPath: 'examples.mnist.pipeline',
    tags: ['example', 'pytorch', 'mnist', 'demo'],
    owner: 'Demo User',
    status: 'RUNNING',
    failedAt: undefined as undefined | string,
    resolvedAt: undefined as undefined | string,
    canceledAt: undefined as undefined | string,
}

const columnHelper = createColumnHelper<typeof RunData>()

const columns = [
    columnHelper.accessor('ID', {
        meta: {
            columnStyles: {
                width: "5.923%",
            }
        },
        header: 'ID',
        cell: info => <StyledRunReferenceLink variant={'inherit'} runId={info.getValue()} />,
    }),
    columnHelper.accessor('created', {
        meta: {
            columnStyles: {
                width: "12.3396%",
                minWidth: "140px"
            }
        },
        header: 'Submitted at',
        cell: info => DateTimeLongConcise(parseJSON(info.getValue())),
    }),
    columnHelper.accessor(data => [data.name, data.importPath], {
        meta: {
            columnStyles: {
                width: "1px",
                maxWidth: "calc(100vw - 1090px)"
            }
        },
        header: 'Name',
        cell: info => {
            const [name, importPath] = info.getValue();
            return <NameSection>
                <PipelineTitle>{name}</PipelineTitle>
                <ImportPath>{importPath}</ImportPath>
            </NameSection>
        },
    }),
    columnHelper.accessor('tags', {
        meta: {
            columnStyles: {
                width: "14.5114%",
                minWidth: "160px"
            }
        },
        header: 'Tags',
        cell: info => <TagsList tags={info.getValue()} fold={2} />,
    }),
    columnHelper.accessor('owner', {
        meta: {
            columnStyles: {
                width: "8.39092%",
                minWidth: "100px"
            }
        },
        header: 'Owner',
        cell: info => info.getValue(),
    }),
    columnHelper.accessor(data => ({
        futureState: data.status,
        createdAt: data.created,
        failedAt: data.failedAt,
        canceledAt: data.canceledAt,
        resolvedAt: data.resolvedAt
    }), {
        meta: {
            columnStyles: {
                width: "15.7947%",
                minWidth: "200px"
            }
        },
        header: 'Status',
        cell: info => <RunStatusColumn {...info.getValue()} />,
    }),
    columnHelper.display({
        meta: {
            columnStyles: {
                width: "2.46792%",
                minWidth: "40px"
            }
        },
        header: '',
        id: 'goto',
        cell: _ => <ChevronRight style={{cursor: 'pointer'}}/>,
    }),
]

const data: Array<typeof RunData> = [
    RunData,
    RunData,
    { ...RunData, resolvedAt: '2021-10-01T12:10:00Z', status: 'SUCCESS' },
    { ...RunData, failedAt: '2021-10-01T12:10:00Z', status: 'FAILED' },
    { ...RunData, canceledAt: '2021-10-01T12:10:00Z', status: 'CANCELLED' },
    { ...RunData, status: 'SCHEDULED' },
    RunData,
    RunData,
    RunData,
    RunData,
    { ...RunData, canceledAt: '2021-10-01T12:10:00Z', status: 'CANCELLED' },
    { ...RunData, status: 'SCHEDULED' },
    RunData,
    RunData,
    { ...RunData, canceledAt: '2021-10-01T12:10:00Z', status: 'CANCELLED' },
]

const RunList = () => {
    const tableInstance = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel()
    });

    return <Container>
        <Stats>
            <Typography variant={'bold'}>142 Runs</Typography>
        </Stats>
        <TableComponent table={tableInstance} />
        <Pagination>
            <ChevronLeft /> 
                {'1 / 4'} 
            <ChevronRight />
        </Pagination>
    </Container>
}

export default RunList;