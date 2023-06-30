import { Box, TextField } from "@mui/material";
import { useCallback, useState } from "react";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";
import BidirectionalLogView from "@sematic/common/src/pages/RunDetails/logs/BidirectionalLogView";
import { useRunPanelContext, useRunPanelLoadingIndicator } from "src/hooks/runDetailsHooks";
import styled from "@emotion/styled";

const StyledContainer = styled(Box)`
    display: flex;
    flexDirection: column;

    & .jump-to-beginning {
        top: 118px;
    }
`;

export default function LogPanel() {
    const { selectedRun } = usePipelinePanelsContext();
    const { id } = selectedRun!;
    const [filterString, setFilterString] = useState<string>("");

    const onFilterStringChange = useCallback(
        (evt: any) => {
            setFilterString(evt.target.value);
        },
        [setFilterString]
    );

    const { setFooterRenderProp, scrollContainerRef } = useRunPanelContext();
    const [isLoading, setIsLoading] = useState<boolean>(false);

    useRunPanelLoadingIndicator(isLoading);

    return (
        <Box >
            <StyledContainer sx={{ display: "flex", flexDirection: "column"}} >
                <TextField
                    variant="standard"
                    fullWidth={true}
                    placeholder={"Filter..."}
                    onChange={onFilterStringChange}
                    style={{ flexShrink: 1 }}
                />
                <BidirectionalLogView key={`${id}---${filterString}`} logSource={id}
                    filterString={filterString} scrollContainerRef={scrollContainerRef} 
                    setFooterRenderProp={setFooterRenderProp} setIsLoading={setIsLoading} />
            </StyledContainer>
        </Box>
    );
}
