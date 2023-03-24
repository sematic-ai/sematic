declare module '@mui/material/styles' {
    interface TypographyVariants {
        small: React.CSSProperties;
        big: React.CSSProperties;
        bold: React.CSSProperties;
        bigBold: React.CSSProperties;
    }

    // allow configuration using `createTheme`
    interface TypographyVariantsOptions {
        small?: React.CSSProperties;
        big?: React.CSSProperties;
        bold?: React.CSSProperties;
        bigBold?: React.CSSProperties;
    }
    interface Palette {
        black: PaletteColor;
        lightGray: PaletteColor;
        p3border: PaletteColor;
    }
}

declare module '@mui/material/Button' {
    interface ButtonPropsVariantOverrides {
        logo: true;
        menu: true;
    }
}

declare module '@mui/material/Typography' {
    interface TypographyPropsVariantOverrides {
        small: true;
        big: true;
        bigBold: true;
        bold: true;
        logo: true;
        menu: true;
    }
}

export const notAModule = 1;
