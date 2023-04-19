import io from "socket.io-client";

export const graphSocket = io("/graph");

export const pipelineSocket = io("/pipeline");

export const jobSocket = io("/job");