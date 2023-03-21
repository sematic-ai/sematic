import { blue, common } from "@mui/material/colors";
import { PaletteColorOptions } from "@mui/material/styles";

const pallette: Record<string, PaletteColorOptions> = {
    primary: {
        main: blue[500]
    },
    lightGrey: {
        main: '#f5f5f5'
    },
    black: {
        main: '#2D2C2E',
        contrastText: common['white']
    },
    p3border: {
        main: 'rgba(0, 0, 0, 0.03)'
    }
}

export default pallette;
