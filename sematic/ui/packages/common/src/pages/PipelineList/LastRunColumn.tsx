import { useMemo } from "react";
import MuiRouterLink from "src/component/MuiRouterLink";
import TimeAgo from "src/component/TimeAgo";
import { getRunUrlPattern } from "src/hooks/runHooks";
import { RowMetadataType } from "src/pages/PipelineList/common";
import sortBy from "lodash/sortBy";
import last from "lodash/last";
import { Run } from "src/Models";

interface LastRunColumnProps {
    metadata: RowMetadataType | undefined;
}

function LastRunColumn(props: LastRunColumnProps) {
    const { metadata } = props;

    return <>{useMemo(() => {
        if (!metadata || !metadata.latestRuns) {
            return;
        }
        const run = last(sortBy(metadata.latestRuns, run => run.created_at)) as Run;
        return <MuiRouterLink href={getRunUrlPattern(run.id)}>
            <TimeAgo date={run.created_at} />
        </MuiRouterLink>;
    }, [metadata])}</>;
}

export default LastRunColumn;