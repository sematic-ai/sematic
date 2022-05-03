import * as React from "react";

import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";

import { useRoutes } from "react-router-dom";

import createTheme from "./theme";
import routes from "./routes";

export function App(): React.ReactElement {
  const theme = "LIGHT";
  
  const content = useRoutes(routes)

  return (
      <MuiThemeProvider theme={createTheme(theme)}>
        {content}
      </MuiThemeProvider>
  );
}
