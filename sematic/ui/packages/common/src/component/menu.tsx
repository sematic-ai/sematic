import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import useTheme from "@mui/material/styles/useTheme";
import Fox from "src/static/fox";
import palette from "src/theme/new/palette";
import { SimplePaletteColorOptions } from "@mui/material/styles";

const StyledGridContainer = styled(Grid)`
    border-bottom: 1px solid ${() => (palette.p3border as SimplePaletteColorOptions).main};
`;

const HeaderMenu = () => {
    const theme = useTheme();

    return <StyledGridContainer container spacing={0}>
        <Box style={{flexGrow: 1, display: 'flex'}} >
            <Button variant="logo" style={{marginRight: theme.spacing(6)}}>
                <Fox style={{width: '16px'}}/>
            </Button>
            
            <Button variant="menu">Runs</Button>
            <Button variant="menu">Pipelines</Button>
            <Button variant="menu">Metrics</Button>
        </Box>
        <Box style={{flexGrow: 1, display: 'flex', justifyContent: 'end'}} >
            <Button variant="menu">Get Started</Button>
            <Button variant="menu">Docs</Button>
            <Button variant="menu">Support</Button>
            <Button variant="menu">Developer E</Button>
        </Box>
    </StyledGridContainer>;
};

export default HeaderMenu;