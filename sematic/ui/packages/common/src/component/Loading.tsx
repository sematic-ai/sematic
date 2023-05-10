import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";

const Loading = () => <Box sx={{ textAlign: "center" }}>
    <CircularProgress sx={{ marginY: 5 }} />
</Box>;

export default Loading;
