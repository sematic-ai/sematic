import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import MenuItem from "@mui/material/MenuItem";
import Select, { SelectChangeEvent, selectClasses } from "@mui/material/Select";
import { svgIconClasses } from "@mui/material/SvgIcon";
import Typography, { typographyClasses } from "@mui/material/Typography";
import isEmpty from "lodash/isEmpty";
import keyBy from "lodash/keyBy";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Run } from "src/Models";
import { getRunStateChipByState } from "src/component/RunStateChips";
import TimeAgo from "src/component/TimeAgo";
import theme from "src/theme/new";

const StyledSelect = styled(Select)`
    width: 100%;

    & .${selectClasses.select} {
        padding-left: 0;
    }
`;

const StyledBox = styled(Box)`
    color: ${theme.palette.lightGrey.main};
    padding-left: 8px;
    display: flex;
    flex-direction: row;
    align-items: center;

    & .${svgIconClasses.root} {
        width: 15px;
        height: 15px;
        margin-right: 10px;
    }

    & .${typographyClasses.root} {
        margin-right: 10px;
    }
`;

const StyledMenuItem = styled(MenuItem)`
    padding-left: 0;
`;

interface ValuePresentationProps {
    run: Run;
}
const ValuePresentation = (props: ValuePresentationProps) => {
    const { run } = props;
    const stateChip = useMemo(() => getRunStateChipByState(run.future_state, "large"), [run.future_state]);
    return <StyledBox {...props}>
        {stateChip}
        <Typography variant="code">{run.id.substring(0, 7)}</Typography>
        <Typography variant="small">
            <TimeAgo date={run.created_at}  />
        </Typography>
    </StyledBox>
}

export interface RunsDropdownProps {
    onChange?: (value: unknown) => void;
    defaultValue?: string;
    runs: Array<Run>;
}

const RunsDropdown = (prop: RunsDropdownProps) => {
    const { onChange: reportChange, defaultValue, runs } = prop;

    const [value, setValue] = useState<string>("");

    const runsMap = useMemo(() => keyBy(runs, "id"), [runs]);

    const renderValue = useCallback((runId: unknown) => {
        const run = runsMap[runId as string];
        if (!run) {
            return null;
        }
        return <ValuePresentation run={run} />;
    }, [runsMap]);

    const onChange = useCallback((event: SelectChangeEvent<unknown>) => {
        const newValue = event.target.value as string;
        setValue(newValue);
        reportChange?.(newValue);
    }, [setValue, reportChange]);

    useEffect(() => {
        if (isEmpty(runs)) {
            return;
        }
        if (value === "") {
            setValue(defaultValue ?? "");
        }
    }, [runs, value, defaultValue, setValue]);

    return <FormControl style={{ width: "100%" }} size="small">
        <StyledSelect value={value} renderValue={renderValue} onChange={onChange}>
            {runs.map((run) => <StyledMenuItem key={`${run.id}--${run.future_state}`} value={run.id}>
                <ValuePresentation run={run} />
            </StyledMenuItem>)}
        </StyledSelect>
    </FormControl>;
}

export default RunsDropdown;