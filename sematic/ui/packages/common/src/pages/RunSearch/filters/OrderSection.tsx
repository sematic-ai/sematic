import styled from '@emotion/styled';
import { KeyboardArrowDown } from "@mui/icons-material";
import CollapseableFilterSection from 'src/pages/RunSearch/filters/CollapseableFilterSection';
import theme from "src/theme/new";
import Typography from '@mui/material/Typography';
import { useState, useCallback } from "react";

const Container = styled.div`
    margin: -${theme.spacing(2.4)} 0;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    height: 50px;
    align-items: center;
`;

type State = 'asc' | 'desc';

type SortButtonProps = {
    state: State;
}

const StyledSortButton = styled(KeyboardArrowDown)<SortButtonProps>`
    cursor: pointer;
    color: ${theme.palette.black.main};
    transform: ${({state}) => state === 'asc' ? "rotate(180deg)" : "rotate(0deg)"};
    transition: transform 200ms cubic-bezier(0.4, 0, 0.2, 1) 0ms;
`;

interface OwnersFilterSectionProps {
    onFiltersChanged?: (filters: string[]) => void;
}

const OrderSection = (props: OwnersFilterSectionProps) => {
    const [state, setState] = useState<State>('desc');

    const onSortClick = useCallback(() => {
        setState((state) => state === 'asc' ? 'desc' : 'asc');
    }, [setState]);

    return <CollapseableFilterSection title={"Order"} >
        <Container>
            <Typography>Most recent</Typography>
            <StyledSortButton state={state} onClick={onSortClick}/>
        </Container>
    </CollapseableFilterSection>;
}

export default OrderSection;
