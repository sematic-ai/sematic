enum FutureState {
    "CREATED",
    "RESOLVED",
    "RAN",
    "SCHEDULED",
    "FAILED",
    "NESTED_FAILED"
}


export type GlowRun = {
    id: string,
    futureState: FutureState,
    name: string,
    parentId: string,
    tags: [string],
    
    createdAt: Date,
    updatedAt: Date,
    startedAt: Date,
    endedAt: Date,
    resolvedAt: Date,
    failedAt: Date,
};
