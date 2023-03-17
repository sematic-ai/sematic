import Box from "@mui/material/Box";
import { ThemeProvider } from "@mui/material/styles";
import { useContext } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { UserContext } from "../appContext";
import { useAppContext } from "../hooks/appHooks";
import createTheme from "@sematic/common/src/theme/mira";
import SideBar from "./SideBar";

export default function Shell() {
  const { authenticationEnabled } = useAppContext()
  const { user } = useContext(UserContext);

  if (authenticationEnabled && !user) {
      return <Navigate to="/login" />;
  }

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
          <SideBar />
        </Box>
        <Box sx={{ gridColumn: 2, overflowY: "scroll" }}>
          <Outlet />
        </Box>
      </Box>
    </ThemeProvider>
  );
}
