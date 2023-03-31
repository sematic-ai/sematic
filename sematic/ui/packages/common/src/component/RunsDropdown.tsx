import styled from '@emotion/styled';
import FormControl from '@mui/material/FormControl';
import MenuItem from '@mui/material/MenuItem';
import Box from '@mui/material/Box';
import Select, {selectClasses} from '@mui/material/Select';
import Typography, { typographyClasses } from '@mui/material/Typography';
import { useCallback } from "react";
import theme from "src/theme/new";
import { svgIconClasses } from "@mui/material/SvgIcon";
import { SuccessStateChip } from 'src/component/RunStateChips';

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
    value: any;
}
const ValuePresentation = (props: ValuePresentationProps) => {
    const { value } = props;
    return <StyledBox {...props}>
        <SuccessStateChip size="small" />
        <Typography variant="code">{`02wqdf5-${value}`}</Typography>
        <Typography variant="small">2d ago</Typography>
    </StyledBox>
}

interface RunsDropdownProps {
    onChange?: (value: unknown) => void;
}

const RunsDropdown = (prop: RunsDropdownProps) => {
    const { onChange } = prop;

    const renderValue = useCallback((value: unknown) => {
        return <ValuePresentation value={value as string} />;
    }, []);

    return <FormControl style={{ width: '100%' }} size="small">
        <StyledSelect defaultValue={"1"} renderValue={renderValue} onChange={onChange}>
            <StyledMenuItem value="1">
                <ValuePresentation value="1" />
            </StyledMenuItem>
            <StyledMenuItem value="2">
                <ValuePresentation value="2" />
            </StyledMenuItem>
            <StyledMenuItem value="3">
                <ValuePresentation value="3" />
            </StyledMenuItem>
        </StyledSelect>
    </FormControl>;
}

export default RunsDropdown;