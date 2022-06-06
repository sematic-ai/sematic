import Box from "@mui/material/Box";
import { useState, useEffect } from "react";
import { Run } from "../Models";
import { RunViewPayload } from "../Payloads";
import Loading from "../components/Loading";

function RunView(props: { id: string }) {
  const [error, setError] = useState<Error | undefined>(Error("ka"));
  const [isLoaded, setIsLoaded] = useState(false);
  const [run, setRun] = useState<Run | undefined>(undefined);

  useEffect(() => {
    fetch("/api/v1/runs/" + props.id)
      .then((res) => res.json())
      .then(
        (result: RunViewPayload) => {
          setRun(result.content);
          setIsLoaded(true);
        },
        (error) => {
          setError(error);
          setIsLoaded(true);
        }
      );
  }, [props.id]);

  if (error || !isLoaded) {
    return <Loading error={error} isLoaded={isLoaded} />;
  }
}

export default RunView;
