import React from "react";
import Dashboard from "./Dashboard";

import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";

import createTheme from "./theme";

export function App(): React.ReactElement {
  const theme = "LIGHT";

  return (
    <div>
        <MuiThemeProvider theme={createTheme(theme)}>
            <Dashboard children={undefined} />
        </MuiThemeProvider>
    </div>
  );
}
