import { Link } from "react-router-dom";
import { getRunUrlPattern } from "../hooks/pipelineHooks";
import { CopyButton } from "./CopyButton";

export default function RunId(props: {
    runId: string;
    trim?: boolean;
    copy?: boolean;
  }) {
    const { runId, trim = true, copy = true } = props;
  
    return (
      <>
        <Link to={getRunUrlPattern(runId)} style={
          {fontSize: '12px'}
        }>
            <code>{trim ? runId.substring(0, 6) : runId}</code>
        </Link>
        {copy && <CopyButton text={runId} message="Copied run ID" />}
      </>
    );
  }
  