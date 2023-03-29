import { getRunUrlPattern } from "../hooks/pipelineHooks";
import CopyButton from "@sematic/common/src/component/CopyButton";
import MuiRouterLink from "./MuiRouterLink";

export default function RunId(props: {
    runId: string;
    trim?: boolean;
    copy?: boolean;
  }) {
    const { runId, trim = true, copy = true } = props;
  
    return (
      <>
        <MuiRouterLink to={getRunUrlPattern(runId)} underline="hover" 
          style={{fontSize: '12px', color: 'revert'}}>
            <code>{trim ? runId.substring(0, 6) : runId}</code>
        </MuiRouterLink>
        {copy && <CopyButton text={runId} message="Copied run ID" />}
      </>
    );
  }
  