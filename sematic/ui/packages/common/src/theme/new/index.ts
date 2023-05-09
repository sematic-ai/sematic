/// <reference path="../../muitypes.d.ts" />
import { createTheme as createMuiTheme } from "@mui/material/styles";
import breakpoints from "src/theme/mira/breakpoints";
import components from "src/theme/new/components";
import palette from "src/theme/new/palette";
import typography from "src/theme/new/typography";

export const SPACING = 5;

export const createTheme = () => {
    return createMuiTheme(
        {
            spacing: SPACING,
            breakpoints,
            palette,
            typography,
            components 
        }
    );
}

export const theme = createTheme();

export default theme;
