import { PaletteColor, Theme } from "@mui/material";


export function getColor(futureState: string, theme: Theme): PaletteColor {
    if (futureState === "RESOLVED") {
      return theme.palette.success;
    }
    if (futureState === "RETRYING") {
      return theme.palette.warning;
    }
    if (["SCHEDULED", "RAN"].includes(futureState)) {
      return theme.palette.info;
    }
    if (["FAILED", "NESTED_FAILED"].includes(futureState)) {
      return theme.palette.error;
    }
    return {
      light: theme.palette.grey[400],
      dark: theme.palette.grey[600],
      main: theme.palette.grey[400],
      contrastText: "",
    };
  }