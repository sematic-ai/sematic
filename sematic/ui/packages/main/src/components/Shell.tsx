import Box from "@mui/material/Box";
import { ThemeProvider } from "@mui/material/styles";
import UserContext from "@sematic/common/src/context/UserContext";
import { useAppContext } from "@sematic/common/src/hooks/appHooks";
import createTheme from "@sematic/common/src/theme/mira";
import { NewDashBoardPromotionOptoutAtom } from "@sematic/common/src/utils/FeatureFlagManager";
import { useAtom } from "jotai";
import { useCallback, useContext } from "react";
import { Navigate, Outlet } from "react-router-dom";
import PromotionBanner from "src/components/PromotionBanner";
import SideBar from "./SideBar";

export default function Shell() {
    const { authenticationEnabled } = useAppContext()
    const { user } = useContext(UserContext);

    const [newDashBoardPromotionOptout, setNewDashBoardPromotionOptout] = useAtom(NewDashBoardPromotionOptoutAtom);

    const onCloseBanner = useCallback(() => {
        setNewDashBoardPromotionOptout(true);
    }, [setNewDashBoardPromotionOptout]);

    if (authenticationEnabled && !user) {
        return <Navigate to="/login" />;
    }

    return (
        <ThemeProvider theme={createTheme("LIGHT")}>
            <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
                {!newDashBoardPromotionOptout && <PromotionBanner onClose={onCloseBanner} />}
                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: "60px auto",
                        gridTemplateRows: "1fr",
                        flexGrow: 1,
                        flexShrink: 1,
                    }}
                >
                    <Box sx={{ gridColumn: 1, gridRow: 1 }}>
                        <SideBar />
                    </Box>
                    <Box sx={{ gridColumn: 2, overflowY: "scroll" }}>
                        <Outlet />
                    </Box>
                </Box>
            </div>

        </ThemeProvider>
    );
}
