import Card from "@mui/material/Card";
import Typography from "@mui/material/Typography";
import ReactMarkdown from "react-markdown";

export default function Docstring(props: {
  docstring: string | undefined | null;
}) {
  const { docstring } = props;

  return (
    <Card variant="outlined" sx={{ padding: 4, fontSize: "small" }}>
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
