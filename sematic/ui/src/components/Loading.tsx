import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";

function Loading(props: { isLoaded: boolean; error?: Error }) {
  if (props.error) {
    return <Alert severity="error">{props.error.message}</Alert>;
  }
  if (!props.isLoaded) {
    return (
      <Box sx={{ textAlign: "center" }}>
        <CircularProgress sx={{ marginY: 5 }} />
      </Box>
    );
  }
  return <></>;
}

export default Loading;
