import { Alert, AlertTitle } from "@mui/material";

export default function Exception(props: { exception: string }) {
  const { exception } = props;
  return (
    <Alert severity="error" icon={false}>
      <AlertTitle>
        {exception.split("\n")[exception.split("\n").length - 2]}
      </AlertTitle>
      <pre
        style={{
          whiteSpace: "pre-wrap",
          overflowWrap: "anywhere",
        }}
      >
        {exception}
      </pre>
    </Alert>
  );
}
