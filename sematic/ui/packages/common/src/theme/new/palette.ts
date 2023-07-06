import { blue, common, grey } from "@mui/material/colors";
import { PaletteColorOptions } from "@mui/material/styles";

const pallette: Record<string, PaletteColorOptions> = {
    primary: {
        main: blue[500]
    },
    lightGrey: {
        main: "#BDB7B4"
    },
    mediumGrey: {
        main: grey[600]
    },
    black: {
        main: "#2D2C2E",
        contrastText: common["white"]
    },
    p3border: {
        main: "rgba(246, 246, 246, 1)"
    },
    p1black: {
        main: "rgba(252, 252, 252, 1)"
    },
    white: {
        main: common["white"],
        contrastText: "#2D2C2E",
        dark: grey[50]
    }
}

export default pallette;
