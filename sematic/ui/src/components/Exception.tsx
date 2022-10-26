import { Alert, AlertTitle } from "@mui/material";
import { ExceptionMetadata } from "../Models";

export function Exception(props: { exception_metadata: ExceptionMetadata }) {
  const { exception_metadata } = props;
  return (
    <Alert severity="error" icon={false}>
      <AlertTitle>
        {exception_metadata.repr.split("\n")[exception_metadata.repr.split("\n").length - 2]}
      </AlertTitle>
      <pre
        style={{
          whiteSpace: "pre-wrap",
          overflowWrap: "anywhere",
        }}
      >
        {exception_metadata.repr}
      </pre>
    </Alert>
  );
}

export function ExternalException(props: { exception_metadata: ExceptionMetadata }) {
  return (
    <Alert severity="error" variant="outlined" sx={{ alignItems: 'center' }} >
      <AlertTitle>
        <pre
          style={{
            whiteSpace: "pre-wrap",
            overflowWrap: "anywhere",
          }}
        >
          {props.exception_metadata.repr}
        </pre>
      </AlertTitle>
    </Alert>
  );
}
