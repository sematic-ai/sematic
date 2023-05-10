import CssBaseline from '@mui/material/CssBaseline';
import Grid from "@mui/material/Grid";
import { ThemeProvider } from "@mui/material/styles";
import find from "lodash/find";
import { useMemo } from "react";
import { Outlet, useMatches } from "react-router-dom";
import HeaderMenu from "src/component/menu";
import SnackBarProvider from "src/context/SnackBarProvider";
import theme from "src/theme/new/index";

export const HeaderSelectionKey = 'activatedHeaderKey';

const Shell = () => {
  const matches = useMatches();

  // see if the current route would want to activate a menu item.
  const selectionKey = useMemo(() => {
    const found = find(matches, (match) => 
      !!match.handle && (match.handle as any)[HeaderSelectionKey] !== undefined);
    return found ? (found.handle as any)[HeaderSelectionKey] : undefined;
  }, [matches]);

  return <SnackBarProvider>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Grid container spacing={0} direction={'column'} style={{ height: "100vh", width: "100%" }}>
        <Grid style={{ flexShrink: 0, flexGrow: 0 }}>
          <HeaderMenu selectedKey={selectionKey} />
        </Grid>
        <Grid style={{ flexGrow: 1, height: 0 }}>
          <Outlet />
        </Grid>
      </Grid>
    </ThemeProvider>
  </SnackBarProvider>;
}

export default Shell;