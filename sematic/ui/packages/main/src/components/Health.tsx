import { useContext, useEffect } from "react";
import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import useAsync from "react-use/lib/useAsync";
import SnackBarContext from "@sematic/common/src/context/SnackBarContext";
import { MessageKind } from "@sematic/main/src/components/SnackBarProvider";

type SingleStatus = {
  healthy: boolean;
  message: string;
};


type HealthReport = {
  api: SingleStatus;
  db: SingleStatus;  
};

export default function Health() {

  const [message, loading, error] = useFetchHealth();

  const { setSnackMessage } = useContext(SnackBarContext);

  useEffect(() => {
    if(!!message) {
      console.log("Message: "+ message)
      setSnackMessage({ message: message, kind: MessageKind.Error});
    }
  }, [message, setSnackMessage]);

  return <></>;
}

function useFetchHealth():[
  string | null,
  boolean,
  Error | undefined
] {
  const {fetch} = useHttpClient();

  const {value, loading, error} = useAsync(async () => {
    const response  = await fetch({
        url: `/api/v1/meta/health`
    });
    return ((await response.json()) as HealthReport);
  }, []);

  var message = null;
  if(!!value) {
    if(!value.api.healthy) {
      message = value.api.message;
    } else if (!value.db.healthy) {
      message = value.db.message;
    }
  } else if(!!error){
    message = "Unable to verify even basic Sematic API access.";
  }
  return [message, loading, error];
}
