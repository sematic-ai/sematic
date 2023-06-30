import styled from "@emotion/styled";
import { useState, useMemo } from "react";
import { Container, Left, Right as RightBase } from "src/layout/ThreeColumns";
import theme from "src/theme/new";
import Box from "@mui/material/Box";
import Loading from "src/component/Loading";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { ExtractContextType } from "src/utils/typings";

const Right = styled(RightBase)`
    width: auto;
    flex-grow: 1;
    padding: 0 ${theme.spacing(5)};
    position: relative;

    & .runs-table {
        min-width: 850px;
    }
`

const LoadingOverlay = styled(Box)`
  position: absolute;
  left: 0;
  bottom: 0;
  top: 0;
  right: 0;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
`


export interface TwoColumnsProps {
    onRenderLeft: () => React.ReactNode;
    onRenderRight: () => React.ReactNode;
}

const TwoColumns = (props: TwoColumnsProps) => {
    const { onRenderLeft, onRenderRight } = props;

    const [isLoading, setIsLoading] = useState<boolean>(false);

    const leftPane = useMemo(() => onRenderLeft(), [onRenderLeft]);
    const rightPane = useMemo(() => onRenderRight(), [onRenderRight]);

    const layoutServiceValue: ExtractContextType<typeof LayoutServiceContext> = useMemo(() => ({
        setIsLoading
    }), [setIsLoading]);

    return (
        <Container>
            <Left>{leftPane}</Left>
            <Right >
                <LayoutServiceContext.Provider value={layoutServiceValue}>
                    {isLoading && <LoadingOverlay>
                        <Loading />
                    </LoadingOverlay>}
                    {rightPane}
                </LayoutServiceContext.Provider>
            </Right>
        </Container >
    );
};

export default TwoColumns;
