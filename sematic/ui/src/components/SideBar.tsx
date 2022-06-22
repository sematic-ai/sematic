import { BatchPrediction } from "@mui/icons-material";
import { Box, Typography, Link, Stack } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { SiDiscord, SiReadthedocs } from "react-icons/si";
import logo from "../Fox.png";
export default function SideBar() {
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateRows: "auto 1fr auto",
        gridTemplateColumns: "auto",
        backgroundColor: theme.palette.grey[800],
        color: "rgba(255, 255, 255, 0.5)",
        textAlign: "center",
        height: "100vh",
      }}
    >
      <Stack sx={{ gridRow: 1, spacing: 2, paddingTop: 3 }}>
        <Box sx={{ color: "#ffffff", paddingBottom: 4 }}>
          <Link href="/" underline="none">
            <img src={logo} width="30px" alt="Sematic fox" />
            {/*<Typography fontSize={32}>🦊</Typography>*/}
          </Link>
        </Box>
        <Box mt={5}>
          <Link
            href="/pipelines"
            sx={{ color: "rgba(255, 255, 255, 0.5)" }}
            underline="none"
          >
            <BatchPrediction fontSize="large" />
            <Typography fontSize={10}>Pipelines</Typography>
          </Link>
        </Box>
      </Stack>
      <Stack
        spacing={4}
        sx={{
          gridRow: 3,
          fontSize: 24,
          paddingBottom: 4,
        }}
      >
        <Box>
          <SiReadthedocs />
          <Typography fontSize={10}>Docs</Typography>
        </Box>
        <Box>
          <Link
            href="https://discord.gg/PFCpatvy"
            sx={{ color: "rgba(255, 255, 255, 0.5)" }}
            underline="none"
          >
            <SiDiscord />
            <Typography fontSize={10}>Discord</Typography>
          </Link>
        </Box>
      </Stack>
    </Box>
  );
}
