import React from "react";

export default function SvgFilters() {
    return <svg version="1.1" width="0" height="0" style={{display: "none"}}>
        <filter id="gaussian-blur-0.5">
            <feGaussianBlur stdDeviation="0.2" />
        </filter>
        <filter id="gaussian-blur-1">
            <feGaussianBlur stdDeviation="0.4" />
        </filter>
        <filter id="gaussian-blur-0">
            <feGaussianBlur stdDeviation="0" />
        </filter>
    </svg>
}