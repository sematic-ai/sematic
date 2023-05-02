import { useMemo } from 'react';
import { Container, Left, Right } from 'src/layout/ThreeColumns';

export interface TwoColumnsProps {
    onRenderLeft: () => React.ReactNode;
    onRenderRight: () => React.ReactNode;
}

const TwoColumns = (props: TwoColumnsProps) => {
    const { onRenderLeft, onRenderRight } = props;

    const leftPane = useMemo(() => onRenderLeft(), [onRenderLeft]);
    const rightPane = useMemo(() => onRenderRight(), [onRenderRight]);

    return (
        <Container>
            <Left>{leftPane}</Left>
            <Right >{rightPane}</Right>
        </Container>
    );
};

export default TwoColumns;
