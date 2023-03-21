import { useMemo } from 'react';
import styled from '@emotion/styled';
import theme from 'src/theme/new';

const Left = styled.div`
    min-width: 300px;
    width: 19.841%;
    height: 100%;
    border-right: 1px solid ${theme.palette.p3border.main};
    padding: 12px 25px;
    box-sizing: border-box;
    overflow-y: auto;
`;

const Center = styled.div`
    height: 100%;
    flex-grow: 1;
`;

const Right = styled.div`
    min-width: 300px;
    width: 19.841%;
    height: 100%;
`;

const Container = styled.div`
    width: 100%;
    height: 100%;
    display: flex;
`;

export interface ThreeColumnsProps {
    onRenderLeft: () => React.ReactNode;
    onRenderCenter?: () => React.ReactNode;
    onRenderRight?: () => React.ReactNode;
}

const ThreeColumns = (props: ThreeColumnsProps) => {
    const { onRenderLeft } = props;

    const leftPane = useMemo(() => onRenderLeft(), [onRenderLeft]);

    return (
        <Container>
            <Left>{leftPane}</Left>
            <Center />
            <Right />
        </Container>
    );
};

export default ThreeColumns;