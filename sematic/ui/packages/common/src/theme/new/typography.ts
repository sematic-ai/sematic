import { TypographyOptions } from "@mui/material/styles/createTypography";

export const fontWeightLight = 300;
export const fontWeightRegular = 400;
export const fontWeightMedium = 500;
export const fontWeightBold = 600;
export const fontFamily = [
  "Inter",
  "-apple-system",
  "BlinkMacSystemFont",
  '"Segoe UI"',
  "Roboto",
  '"Helvetica Neue"',
  "Arial",
  "sans-serif",
  '"Apple Color Emoji"',
  '"Segoe UI Emoji"',
  '"Segoe UI Symbol"',
].join(",")

export const fontFamilyCode = [
  "monospace",
  fontFamily
].join(",")

const typography: TypographyOptions = {
  fontFamily,
  fontSize: 14,
  fontWeightLight,
  fontWeightRegular,
  fontWeightMedium,
  fontWeightBold,
  h1: {
    fontSize: "2rem",
    fontWeight: 600,
    lineHeight: 1.25,
  },
  h2: {
    fontSize: "1.75rem",
    fontWeight: 600,
    lineHeight: 1.25,
  },
  h3: {
    fontSize: "1.5rem",
    fontWeight: 600,
    lineHeight: 1.25,
  },
  h4: {
    fontSize: "1.125rem",
    fontWeight: 500,
    lineHeight: 1.25,
  },
  h5: {
    fontSize: "1.0625rem",
    fontWeight: 500,
    lineHeight: 1.25,
  },
  h6: {
    fontSize: "1rem",
    fontWeight: 500,
    lineHeight: 1.25,
  },
  body1: {
    fontSize: 13,
  },
  button: {
    textTransform: "none",
  },
  small: {
    fontSize: 12,
    fontFamily
  },
  big: {
    fontSize: 16,
    fontFamily
  },
  bold: {
    fontFamily,
    fontSize: 14,
    fontWeight: fontWeightBold,
  },
  bigBold: {
    fontFamily,
    fontSize: 16,
    fontWeight: fontWeightBold,
  },
  code: {
    fontSize: 14,
    fontFamily: fontFamilyCode,
  }
};

export default typography;
