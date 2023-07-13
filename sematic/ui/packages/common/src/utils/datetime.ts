import every from "lodash/every";

function _commonConvertor(displayY: number, displayMon: number, displayD: number,
    displayH: number, displayM: number, displayS: number) {
    if (every([displayY, displayMon, displayD, displayH, displayM, displayS, (a: number) => a === 0])) {
        return "<1s";
    }
    const final = [
        [displayY, "Y"],
        [displayMon, "M"],
        [displayD, "d"],
        [displayH, "h"],
        [displayM, "m"],
        [displayS, "s"]
    ].map(
        ([value, unit]) => (value as number) > 0 ? value.toString() + unit : ""
    ).join(" ").trim();

    return final;

}
export function durationToString(duration: Duration): string {
    const displayY: number = duration.years!;
    const displayMon: number = duration.months!;
    const displayD: number = duration.days!;
    const displayH: number = duration.hours!;
    const displayM: number = duration.minutes!;
    const displayS: number = duration.seconds!;
    return _commonConvertor(displayY, displayMon, displayD, displayH, displayM, displayS);
}


export function durationSecondsToString(durationS: number): string {
    const displayH: number = Math.floor(durationS / 3600);
    const displayM: number = Math.floor((durationS % 3600) / 60);
    const displayS: number = Math.round(durationS % 60);
    return _commonConvertor(0, 0, 0, displayH, displayM, displayS);
}
