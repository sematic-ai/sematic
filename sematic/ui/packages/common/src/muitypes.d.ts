declare module '@mui/material/styles' {
    interface TypographyVariants {
        small: React.CSSProperties;
        big: React.CSSProperties;
        bold: React.CSSProperties;
        bigBold: React.CSSProperties;
        code: React.CSSProperties;
    }

    // allow configuration using `createTheme`
    interface TypographyVariantsOptions {
        small?: React.CSSProperties;
        big?: React.CSSProperties;
        bold?: React.CSSProperties;
        bigBold?: React.CSSProperties;
        code?: React.CSSProperties;
    }
    interface Palette {
        black: PaletteColor;
        lightGrey: PaletteColor;
        mediumGrey: PaletteColor;
        p3border: PaletteColor;
        white: PaletteColor;
    }
}

declare module '@mui/material/Button' {
    interface ButtonPropsVariantOverrides {
        logo: true;
        menu: true;
    }
    interface ButtonPropsColorOverrides {
        white: true;
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
        code: true;
    }
}

declare module '@mui/material/Chip' {
    interface ChipPropsVariantOverrides {
        tag: true;
    }
}

declare module '@mui/material/SvgIcon' {
    interface SvgIconPropsColorOverrides {
        lightGrey: true;
    }
}

export const notAModule = 1;
