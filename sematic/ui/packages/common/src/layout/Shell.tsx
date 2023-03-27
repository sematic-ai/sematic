import theme from "src/theme/new/index";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from '@mui/material/CssBaseline';
import Grid from "@mui/material/Grid";
import { Outlet } from "react-router-dom";
import HeaderMenu from "src/component/menu";
import SnackBarProvider from "src/context/SnackBarProvider";

const Shell = () => {
  return <SnackBarProvider>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Grid container spacing={0} direction={'column'} style={{ height: "100vh", width: "100%" }}>
        <Grid style={{ flexShrink: 1 }}>
          <HeaderMenu />
        </Grid>
        <Grid style={{ flexGrow: 1, height: 0 }}>
          <Outlet />
        </Grid>
      </Grid>
    </ThemeProvider>
  </SnackBarProvider>;
}

export default Shell;