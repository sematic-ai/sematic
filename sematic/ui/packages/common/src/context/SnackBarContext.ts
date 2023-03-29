import { createContext } from "react";

const SnackBarContext = createContext<{
    setSnackMessage?: any;
}>({});

export default SnackBarContext;
  