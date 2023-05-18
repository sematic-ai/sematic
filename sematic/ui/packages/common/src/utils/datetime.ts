function _commonConvertor(displayH: number, displayM: number, displayS: number) {
    if (displayH === 0 && displayM === 0 && displayS === 0) {
        return "<1s";
    }
    const final = [
        displayH > 0 ? displayH.toString() + "h" : "",
        displayM > 0 ? displayM.toString() + "m " : "",
        displayS > 0 ? displayS.toString() + "s" : "",
    ]
        .join(" ")
        .trim();

    return final;

}
export function durationToString(duration: Duration) : string {
    const displayH: number = duration.hours!;
    const displayM: number = duration.minutes!;
    const displayS: number = duration.seconds!;
    return _commonConvertor(displayH, displayM, displayS);
}


export function durationSecondsToString(durationS: number) : string {
    const displayH: number = Math.floor(durationS / 3600);
    const displayM: number = Math.floor((durationS % 3600) / 60);
    const displayS: number = Math.round(durationS % 60);
    return _commonConvertor(displayH, displayM, displayS);
}
