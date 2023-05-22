import React from "react";
import { Graph } from "@sematic/common/src/interfaces/graph";

export const GraphContext = React.createContext<{
    graph: Graph | undefined;
    isLoading: boolean;
} | null>(null);

export default GraphContext;
