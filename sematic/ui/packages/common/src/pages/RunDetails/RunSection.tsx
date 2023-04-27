import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import Typography, { typographyClasses } from "@mui/material/Typography";
import Headline from "src/component/Headline";
import MoreVertButton from "src/component/MoreVertButton";
import RunsDropdown from "src/component/RunsDropdown";
import Section from "src/component/Section";
import TagsList from "src/component/TagsList";
import theme from "src/theme/new";

const StyledSection = styled(Section)`
  margin-bottom: ${theme.spacing(3)};
`;

const StyledVertButton = styled(MoreVertButton)`
  transform: translate(50%, 0);
`;

const BoxContainer = styled(Box)`
  display: flex;
`;

const StyledTypography = styled(Typography)`
  margin-right: ${theme.spacing(2)};
`;

const RunSection = () => {
  const theme = useTheme();

  return (
    <StyledSection>
      <Headline>Pipeline Run</Headline>
      <BoxContainer style={{ marginBottom: theme.spacing(3) }}>
        <RunsDropdown />
        <StyledVertButton />
      </BoxContainer>
      <BoxContainer style={{ marginBottom: theme.spacing(2) }}>
        <StyledTypography variant="small">Developer E.</StyledTypography>
        <Typography variant="small">CloudResolver</Typography>
      </BoxContainer>
      <BoxContainer>
        <TagsList tags={["example", "torch", "mnist"]} />
      </BoxContainer>
    </StyledSection>
  );
};

export default RunSection;
