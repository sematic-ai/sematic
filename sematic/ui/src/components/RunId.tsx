import { useParams, Link } from "react-router-dom";
import { getPipelineUrlPattern } from "../hooks/pipelineHooks";
import { CopyButton } from "./CopyButton";

export default function RunId(props: {
    runId: string;
    trim?: boolean;
    copy?: boolean;
  }) {
    const { runId, trim = true, copy = true } = props;
  
    const { pipelinePath } = useParams();
  
    return (
      <>
        <Link to={getPipelineUrlPattern(pipelinePath!, runId)} style={
          {fontSize: '12px'}
        }>
            <code>{trim ? runId.substring(0, 6) : runId}</code>
        </Link>
        {copy && <CopyButton text={runId} message="Copied run ID" />}
      </>
    );
  }
  