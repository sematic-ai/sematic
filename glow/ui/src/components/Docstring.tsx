import Card from "@mui/material/Card";
import Typography from "@mui/material/Typography";
import ReactMarkdown from "react-markdown";
import { Run } from "../Models";

export default function Docstring(props: { run: Run }) {
  const { run } = props;

  return (
    <Card variant="outlined" sx={{ padding: 4, fontSize: "small" }}>
      {(run.description && (
        <ReactMarkdown>{run.description}</ReactMarkdown>
      )) || (
        <Typography color="GrayText">
          Your function's docstring will appear here.
        </Typography>
      )}
    </Card>
  );
}
