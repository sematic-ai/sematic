import { useMemo, useState } from "react";
import styled from "@emotion/styled";
import theme from "src/theme/new";
import ChevronLeft from "@mui/icons-material/ChevronLeft";
import ChevronRight from "@mui/icons-material/ChevronRight";
import IconButton from "@mui/material/IconButton";


export const Left = styled.div`
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
    border-right: 1px solid ${theme.palette.p3border.main};
    position: relative;
`;

export const Right = styled.div`
    display: flex;
    flex-direction: column;
    min-width: 300px;
    width: 300px;
    height: 100%;
    padding: 0 ${theme.spacing(2.4)};
    box-sizing: border-box;
`;

export const Container = styled.div`
    width: 100%;
    height: 100%;
    display: flex;
`;

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

    const leftPane = useMemo(() => onRenderLeft(), [onRenderLeft]);
    const centerPane = useMemo(() => onRenderCenter(), [onRenderCenter]);
    const rightPane = useMemo(() => onRenderRight(), [onRenderRight]);

    return (
        <Container>
            <Left>{leftPane}</Left>
            <Center>{centerPane}
                <FoldingControlContainer folded={rightPaneFolded} onClick={() => setRightPaneFolded(!rightPaneFolded)}>
                    <StyledIconButton size="small">
                        {rightPaneFolded ? <ChevronLeft /> : <ChevronRight />}
                    </StyledIconButton>
                </FoldingControlContainer>
            </Center>
            <RightWithState folded={rightPaneFolded}>
                {rightPane}
            </RightWithState>
        </Container>
    );
};

export default ThreeColumns;