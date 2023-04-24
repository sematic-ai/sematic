import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Grid from "@mui/material/Grid";
import useTheme from "@mui/material/styles/useTheme";
import Fox from "src/static/fox";
import palette from "src/theme/new/palette";
import { SimplePaletteColorOptions } from "@mui/material/styles";

const StyledGridContainer = styled(Grid)`
    border-bottom: 1px solid ${() => (palette.p3border as SimplePaletteColorOptions).main};
    flex-wrap: nowrap;
`;

interface HeaderMenuProps {
    selectedKey?: string;
}

const HeaderMenu = (props: HeaderMenuProps) => {
    const {selectedKey} = props;
    const theme = useTheme();

    return <StyledGridContainer container spacing={0}>
        <Box style={{flexGrow: 1, display: 'flex'}} >
            <Link variant={'logo'} style={{marginRight: theme.spacing(6)}}>
                <Fox style={{width: '16px'}}/>
            </Link>
            
            <Link variant="subtitle1" type='menu' className={selectedKey === 'runs'? 'selected' : ''}>Runs</Link>
            <Link variant="subtitle1" type='menu' className={selectedKey === 'pipelines'? 'selected' : ''}>Pipelines</Link>
            <Link variant="subtitle1" type='menu' className={selectedKey === 'metrics'? 'selected' : ''}>Metrics</Link>
        </Box>
        <Box style={{flexGrow: 1, display: 'flex', justifyContent: 'end'}} >
            <Link variant="subtitle1" type='menu'>Get Started</Link>
            <Link variant="subtitle1" type='menu'>Docs</Link>
            <Link variant="subtitle1" type='menu'>Support</Link>
            <Link variant="subtitle1" type='menu'>Developer E</Link>
        </Box>
    </StyledGridContainer>;
};

export default HeaderMenu;