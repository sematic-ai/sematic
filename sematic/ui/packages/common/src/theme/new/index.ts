/// <reference path="../../muitypes.d.ts" />
import { createTheme as createMuiTheme } from "@mui/material/styles";
import breakpoints from "src/theme/mira/breakpoints";
import components from "src/theme/new/componnets";
import palette from "src/theme/new/palette";
import typography from "src/theme/new/typography";

const createTheme = () => {
    return createMuiTheme(
        {
            spacing: 4,
            breakpoints,
            palette,
            typography,
            components 
        }
    );
}

export default createTheme;
