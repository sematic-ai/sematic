import io from "socket.io-client";

export const graphSocket = io("/graph");
export const jobSocket = io("/job");
export const pipelineSocket = io("/pipeline");

// TODO: remove once job update socket is hooked to something
if ((new URLSearchParams(window.location.href)).has('debug')) {
    const _onJobUpdate = (args: { source_run_id: string }) => {
        console.log("DEV DEBUG: job update for run: ", args.source_run_id);
    }
    
    jobSocket.on("update", _onJobUpdate);    
}