import { Alert, AlertTitle } from "@mui/material";
import { ExceptionMetadata } from "../Models";

export default function Exception(props: { exception: ExceptionMetadata }) {
  const { exception } = props;
  return (
    <Alert severity="error" icon={false}>
      <AlertTitle>
        {exception.repr.split("\n")[exception.repr.split("\n").length - 2]}
      </AlertTitle>
      <pre
        style={{
          whiteSpace: "pre-wrap",
          overflowWrap: "anywhere",
        }}
      >
        {exception.repr}
      </pre>
    </Alert>
  );
}
