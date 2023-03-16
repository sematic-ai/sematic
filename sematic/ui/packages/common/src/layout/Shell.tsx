import createTheme from "src/theme/new/index";
import { ThemeProvider } from "@mui/material/styles";
import Grid from "@mui/material/Grid";
import { Outlet } from "react-router-dom";
import HeaderMenu from "src/component/menu";

const Shell = () => {
  return <ThemeProvider theme={createTheme()}>
    <Grid container spacing={0} direction={'column'} style={{height: "100%", width: "100%"}}>
      <Grid style={{flexShrink: 1}}>
        <HeaderMenu />
      </Grid>
      <Grid style={{flexGrow: 1}}>
        <Outlet />
      </Grid>
    </Grid>
  </ThemeProvider>;
}

export default Shell;