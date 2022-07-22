import Box from "@mui/material/Box";
import { ThemeProvider } from "@mui/material/styles";
import { Outlet } from "react-router-dom";
import createTheme from "../themes/mira";
import SideBar from "./SideBar";

export default function Shell(props: { onLogout: () => void }) {
  return (
    <ThemeProvider theme={createTheme("LIGHT")}>
      <Box
        sx={{
          height: "100vh",
          display: "grid",
          gridTemplateColumns: "60px auto",
          gridTemplateRows: "1fr",
        }}
      >
        <Box sx={{ gridColumn: 1, gridRow: 1 }}>
          <SideBar onLogout={props.onLogout} />
        </Box>
        <Box sx={{ gridColumn: 2, overflowY: "scroll" }}>
          <Outlet />
        </Box>
      </Box>
    </ThemeProvider>
  );
}
