import styled from "@emotion/styled";
import { useMemo } from "react";
import { Container, Left, Right as RightBase } from "src/layout/ThreeColumns";
import theme from "src/theme/new";

const Right = styled(RightBase)`
    width: auto;
    flex-grow: 1;
    padding: 0 ${theme.spacing(5)};
`

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
