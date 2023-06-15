import io from "socket.io-client";

export const pipelineSocket = io("/pipeline");

export const jobSocket = io("/job");

export const metricsSocket = io("/metrics");
