import { Run } from "src/Models";

export interface Metrics {
    totalCount: number | undefined;
    successRate: string;
    avgRuntime: string;
}

export interface RowMetadataType {
    metrics?: Metrics | undefined;
    latestRuns?: Run[] | undefined;
}

export interface ExtendedRunMetadata {
    run: Run;
    metadata: RowMetadataType | undefined;
}
