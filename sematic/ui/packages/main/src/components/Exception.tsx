import { Alert, AlertTitle, Link } from "@mui/material";
import { ExceptionMetadata } from "../Models";

const DISCORD_MESSAGE = (
  "For assistance with this error message, you can reach out to us on "
);

function DiscordHelp() {
  return (
    <pre>
      {DISCORD_MESSAGE}
      <Link href="https://discord.gg/4KZJ6kYVax">Discord</Link>.
    </pre>
  );
}

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

export function ExternalException(
  props: { exception_metadata: ExceptionMetadata, discord_reference?: Boolean }
) {
  const { exception_metadata, discord_reference = true } = props;
  return (
    <Alert severity="error" icon={false}>
      <AlertTitle>
        <pre
          style={{
            whiteSpace: "pre-wrap",
            overflowWrap: "anywhere",
          }}
        >
          {exception_metadata.repr}
          {discord_reference && <DiscordHelp/>}
        </pre>
      </AlertTitle>
    </Alert>
  );
}
