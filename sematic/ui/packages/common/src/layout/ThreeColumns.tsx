import { useMemo, useState } from "react";
import styled from "@emotion/styled";
import theme from "src/theme/new";
import ChevronLeft from "@mui/icons-material/ChevronLeft";
import ChevronRight from "@mui/icons-material/ChevronRight";
import IconButton from "@mui/material/IconButton";
import Loading from "src/component/Loading";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { ExtractContextType } from "src/utils/typings";
import Box from "@mui/material/Box";

export const Left = styled.div`
    min-width: 300px;
    width: 300px;
    height: 100%;
    border-right: 1px solid ${theme.palette.p3border.main};
    padding: 0 25px;
    box-sizing: border-box;
    overflow: hidden;
    background: ${theme.palette.p1black.main};

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
    flex-shrink: 1;
    padding: 0 25px;
    border-right: 1px solid ${theme.palette.p3border.main};
    position: relative;
    width: 0;
    display: flex;
    flex-direction: column;

    @media (max-width: 1700px) {
        min-width: 800px;

        & .runs-table {
            min-width: 800px;
        }
    }

    @media (max-width: 1200px) {
        min-width: 700px;

        & .runs-table {
            min-width: 700px;
        }
    }
`;

export const Right = styled.div`
    display: flex;
    flex-direction: column;
    min-width: 300px;
    width: 300px;
    height: 100%;
    padding: 0 ${theme.spacing(2.4)};
    box-sizing: border-box;
    background: ${theme.palette.p1black.main};
`;

export const Container = styled.div`
    width: 100%;
    height: 100%;
    display: flex;
`;

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

interface UIState {
    folded: boolean;
}

export const RightWithState = styled(Right, {
    shouldForwardProp: (prop) => prop !== "folded",
}) <UIState>`
    ${({ folded }) => folded ? "display: none;" : ""}
`;

const StyledIconButton = styled(IconButton)`
    border-radius: 0;
    padding: ${theme.spacing(1)} 0;
`;

const FoldingControlContainer = styled("div", {
    shouldForwardProp: (prop) => prop !== "folded",
}) <UIState>`
    position: absolute;
    right: 0;
    top: 50%;
    translate: ${({ folded }) => folded ? "0" : "50%"} -50%;
    opacity: 0.5;
    z-index: 255;

    &:hover {
        opacity: 1;
    }

    &:before {
        background: ${theme.palette.white.main};
        position: absolute;
        content: '';
        top: 5px;
        left: 5px;
        right: 5px;
        bottom: 5px;
    }
`;

export interface ThreeColumnsProps {
    onRenderLeft: () => React.ReactNode;
    onRenderCenter: () => React.ReactNode;
    onRenderRight: () => React.ReactNode;
}

const ThreeColumns = (props: ThreeColumnsProps) => {
    const { onRenderLeft, onRenderCenter, onRenderRight } = props;

    const [rightPaneFolded, setRightPaneFolded] = useState(false);
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const leftPane = useMemo(() => onRenderLeft(), [onRenderLeft]);
    const centerPane = useMemo(() => onRenderCenter(), [onRenderCenter]);
    const rightPane = useMemo(() => onRenderRight(), [onRenderRight]);

    const layoutServiceValue: ExtractContextType<typeof LayoutServiceContext> = useMemo(() => ({
        setIsLoading
    }), [setIsLoading]);

    return (
        <Container>
            <Left>{leftPane}</Left>
            <Center>
                <LayoutServiceContext.Provider value={layoutServiceValue}>
                    {centerPane}
                    <FoldingControlContainer folded={rightPaneFolded} onClick={() => setRightPaneFolded(!rightPaneFolded)}>
                        <StyledIconButton size="small">
                            {rightPaneFolded ? <ChevronLeft /> : <ChevronRight />}
                        </StyledIconButton>
                    </FoldingControlContainer>
                    {isLoading && <LoadingOverlay>
                        <Loading />
                    </LoadingOverlay>}
                </LayoutServiceContext.Provider>
            </Center>
            <RightWithState folded={rightPaneFolded}>
                {rightPane}
            </RightWithState>
        </Container>
    );
};

export default ThreeColumns;