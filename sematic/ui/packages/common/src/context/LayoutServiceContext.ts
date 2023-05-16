import { createContext } from "react";
import noop from "lodash/noop";

const LayoutServiceContext = createContext<{
    setIsLoading: (isLoading: boolean) => void;
}>({
            setIsLoading: noop
        });

export default LayoutServiceContext;
  