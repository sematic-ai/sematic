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

  const message = useFetchHealth();

  const { setSnackMessage } = useContext(SnackBarContext);

  useEffect(() => {
    if(!!message) {
      setSnackMessage({ message: message, autoHide: false, kind: MessageKind.Error});
    }
  }, [message, setSnackMessage]);

  return <></>;
}

function useFetchHealth(): string | null {
  const {fetch} = useHttpClient();

  const {value, error} = useAsync(async () => {
    const response  = await fetch({
        url: `/api/v1/meta/health`
    });
    return ((await response.json()) as HealthReport);
  }, []);

  let message = null;
  if(!!value) {
    if(!value.api.healthy) {
      message = value.api.message;
    } else if (!value.db.healthy) {
      message = value.db.message;
    }
  } else if(!!error){
    message = "Unable to connect to the Sematic API.";
  }
  return message;
}
