import { useMemo } from 'react';
import styled from '@emotion/styled';
import theme from 'src/theme/new';

const Left = styled.div`
    min-width: 300px;
    width: 300px;
    height: 100%;
    border-right: 1px solid ${theme.palette.p3border.main};
    padding: 0 25px;
    box-sizing: border-box;
    overflow: hidden;

    display: flex;
    flex-direction: column;

    & > section {
        flex-grow: 0;
        flex-shrink: 0;
    }
`;

const Center = styled.div`
    height: 100%;
    flex-grow: 1;
    padding: 0 25px;
`;

const Right = styled.div`
    display: flex;
    flex-direction: column;
    min-width: 300px;
    width: 300px;
    height: 100%;
    padding: 0 ${theme.spacing(2.4)};
    box-sizing: border-box;
    border-left: 1px solid ${theme.palette.p3border.main};
`;

const Container = styled.div`
    width: 100%;
    height: 100%;
    display: flex;
`;

export interface ThreeColumnsProps {
    onRenderLeft: () => React.ReactNode;
    onRenderCenter: () => React.ReactNode;
    onRenderRight: () => React.ReactNode;
}

const ThreeColumns = (props: ThreeColumnsProps) => {
    const { onRenderLeft, onRenderCenter, onRenderRight } = props;

    const leftPane = useMemo(() => onRenderLeft(), [onRenderLeft]);
    const centerPane = useMemo(() => onRenderCenter(), [onRenderCenter]);
    const rightPane = useMemo(() => onRenderRight(), [onRenderRight]);

    return (
        <Container>
            <Left>{leftPane}</Left>
            <Center>{centerPane}</Center>
            <Right >{rightPane}</Right>
        </Container>
    );
};

export default ThreeColumns;