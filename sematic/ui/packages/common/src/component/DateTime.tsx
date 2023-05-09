import { useTheme } from "@mui/material/styles";
import Typography from "@mui/material/Typography";
import { format, parseJSON, intervalToDuration, formatDuration } from "date-fns";

interface DateTimeProps {
    datetime: Date | string;
}

const DateTime = (props: DateTimeProps) => {
    const { datetime } = props;
    const theme = useTheme();

    let date = datetime instanceof Date ? datetime : parseJSON(datetime);

    return <Typography variant="small" color={theme.palette.lightGrey.main} >
        {format(date, "MMM d h:mmaaa")}
    </Typography>
}

export const DateTimeLong = (datetime: Date) => {
    return format(datetime, "M/d/yyyy 'at' h:mmaaa")
}

export const DateTimeLongConcise = (datetime: Date) => {
    return format(datetime, "M/d/yyyy h:mmaaa")
}

export const Duration = (start: Date, end: Date) => {
    const duration = intervalToDuration({
        start,
        end
    });

    const formatString = formatDuration(duration, { format: ["minutes", "seconds"], zero: true});

    return formatString.replace(/\s0\sseconds$/g, "");
}

export function DurationShort(start: Date, end: Date) {
    return Duration(start, end).replace(/minutes/g, "m").replace(/seconds/g, "s");
}


export default DateTime;
