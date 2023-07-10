import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import { useCallback, useMemo, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Headline from "src/component/Headline";
import MoreVertButton from "src/component/MoreVertButton";
import NameTag from "src/component/NameTag";
import RunsDropdown from "src/component/RunsDropdown";
import Section from "src/component/Section";
import TagsList from "src/component/TagsList";
import RootRunContext, { useRootRunContext } from "src/context/RootRunContext";
import usePipelineSocketMonitor from "src/hooks/pipelineSocketMonitorHooks";
import { getRunUrlPattern, useFetchRuns } from "src/hooks/runHooks";
import RunSectionActionMenu from "src/pages/RunDetails/contextMenus/RunSectionMenu";
import theme from "src/theme/new";
import { ExtractContextType, RemoveUndefined } from "src/utils/typings";

const StyledSection = styled(Section)`
  margin-bottom: ${theme.spacing(3)};
`;

const StyledVertButton = styled(MoreVertButton)`
  transform: translate(50%, 0);
`;

const BoxContainer = styled(Box)`
  display: flex;
  align-items: center;
`;

const OwnerContainer = styled.span`
  margin-right: ${theme.spacing(2)};
`;

const RunSection = () => {
    const theme = useTheme();
    const navigate = useNavigate();

    const { rootRun, resolution, isGraphLoading } = useRootRunContext() as RemoveUndefined<ExtractContextType<typeof RootRunContext>>;

    const runFilters = useMemo(
        () => ({
            AND: [
                { parent_id: { eq: null } },
                { function_path: { eq: rootRun.function_path } },
            ],
        }),
        [rootRun.function_path]
    );

    const otherQueryParams = useMemo(
        () => ({
            limit: "10",
        }),
        []
    );

    const owner = useMemo(() => <NameTag firstName={rootRun.user?.first_name} lastName={rootRun.user?.last_name} />
        , [rootRun]);

    const resolverKind = useMemo(() => {
        if (!resolution) {
            return "-";
        }
        return resolution.kind === "KUBERNETES" ? "CloudResolver" : "LocalResolver";

    }, [resolution])

    const { runs, reloadRuns } = useFetchRuns(runFilters, otherQueryParams);

    const onRootRunChange = useCallback((newRootRunId: unknown) => {
        navigate(getRunUrlPattern(newRootRunId as string));
    }, [navigate]);

    const contextMenuAnchor = useRef<HTMLButtonElement>(null);

    usePipelineSocketMonitor(rootRun.function_path, useMemo(() => ({
        onCancel: reloadRuns
    }), [reloadRuns]));

    useEffect(() => {
        if (isGraphLoading) {
            return;
        }
        reloadRuns();
    }, [isGraphLoading, reloadRuns])

    return (
        <StyledSection>
            <Headline>Pipeline Run</Headline>
            <BoxContainer style={{ marginBottom: theme.spacing(3) }}>
                <RunsDropdown runs={runs || []} onChange={onRootRunChange} defaultValue={rootRun.id} />
                <StyledVertButton ref={contextMenuAnchor} />
                <RunSectionActionMenu anchorEl={contextMenuAnchor.current} />
            </BoxContainer>
            <BoxContainer style={{ marginBottom: theme.spacing(2) }}>
                <OwnerContainer>{owner}</OwnerContainer>
                <Typography variant="small">{resolverKind}</Typography>
            </BoxContainer>
            <BoxContainer>
                <div><TagsList tags={rootRun.tags} /></div>
                {/** Adding tag is not currently supported will re-enable later */}
                {/* <Button variant={"text"} size={"small"}>add tags</Button> */}
            </BoxContainer>
        </StyledSection>
    );
};

export default RunSection;
