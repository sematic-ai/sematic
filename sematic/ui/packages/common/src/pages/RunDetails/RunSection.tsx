import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import Headline from "src/component/Headline";
import MoreVertButton from "src/component/MoreVertButton";
import RunsDropdown from "src/component/RunsDropdown";
import Section from "src/component/Section";
import TagsList from "src/component/TagsList";
import { useFetchRuns } from "src/hooks/runHooks";
import theme from "src/theme/new";
import { useMemo } from "react";
import RootRunContext, { useRootRunContext } from "src/context/RootRunContext";
import { ExtractContextType, RemoveUndefined } from "src/utils/typings";
import NameTag from "src/component/NameTag";

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

const StyledTypography = styled(Typography)`
  margin-right: ${theme.spacing(2)};
`;

const RunSection = () => {
    const theme = useTheme();

    const { rootRun, resolution } = useRootRunContext() as RemoveUndefined<ExtractContextType<typeof RootRunContext>>;

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

    const { runs } = useFetchRuns(runFilters, otherQueryParams);

    return (
        <StyledSection>
            <Headline>Pipeline Run</Headline>
            <BoxContainer style={{ marginBottom: theme.spacing(3) }}>
                <RunsDropdown runs={runs || []} />
                <StyledVertButton />
            </BoxContainer>
            <BoxContainer style={{ marginBottom: theme.spacing(2) }}>
                <StyledTypography>
                    {owner}
                </StyledTypography>
                <Typography variant="small">{resolverKind}</Typography>
            </BoxContainer>
            <BoxContainer>
                <div><TagsList tags={rootRun.tags} /></div>
                <Button variant={"text"} size={"small"}>add tags</Button>
            </BoxContainer>
        </StyledSection>
    );
};

export default RunSection;
