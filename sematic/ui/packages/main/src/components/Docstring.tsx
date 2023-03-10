import { lighten, useTheme } from "@mui/material";
import Card from "@mui/material/Card";
import Typography from "@mui/material/Typography";
import ReactMarkdown from "react-markdown";

export default function Docstring(props: {
  docstring: string | undefined | null;
}) {
  const { docstring } = props;
  const theme = useTheme();

  return (
    <Card
      variant="outlined"
      sx={{
        padding: 4,
        fontSize: "small",
        backgroundColor: lighten(theme.palette.warning.light, 0.95),
      }}
    >
      {(docstring !== undefined && docstring !== null && (
        <ReactMarkdown>{docstring}</ReactMarkdown>
      )) || (
        <Typography color="GrayText">
          Your function's docstring will appear here.
        </Typography>
      )}
    </Card>
  );
}
