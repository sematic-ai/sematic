import styled from '@emotion/styled';
import FormControl from '@mui/material/FormControl';
import MenuItem from '@mui/material/MenuItem';
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

const StyledMenuItem = styled(MenuItem)`
    color: ${theme.palette.lightGrey.main};
    padding-left: 8px;

    & .${svgIconClasses.root} {
        width: 15px;
        height: 15px;
        margin-right: 10px;
    }

    & .${typographyClasses.root} {
        margin-right: 10px;
    }
`;

interface ValuePresentationProps {
    value: any;
}
const ValuePresentation = (props: ValuePresentationProps) => {
    const { value } = props;
    return <StyledMenuItem value={value}>
        <SuccessStateChip size="small" />
        <Typography variant="code">02wqdf5</Typography>
        <Typography variant="small">2d ago</Typography>
    </StyledMenuItem>
}

const RunsDropdown = () => {
    const renderValue = useCallback((value: unknown) => {
        return <ValuePresentation value={value} />;
    }, []);

    return <FormControl style={{ width: '100%' }} size="small">
        <StyledSelect defaultValue={"1"} renderValue={renderValue} >
            <ValuePresentation value="1" />
            <ValuePresentation value="2" />
            <ValuePresentation value="3" />
        </StyledSelect>
    </FormControl>;
}

export default RunsDropdown;