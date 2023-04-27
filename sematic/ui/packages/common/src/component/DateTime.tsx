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

export const DateTimeLong = (datetime: Date | string) => {
    let date = datetime instanceof Date ? datetime : parseJSON(datetime);

    return format(date, "M/d/yyyy 'at' h:mmaaa")
}

export const Duration = (start: Date | string, end: Date | string) => {
    let startTime = start instanceof Date ? start : parseJSON(start);

    let endTime = end instanceof Date ? end : parseJSON(end);

    const duration = intervalToDuration({
        start: startTime,
        end: endTime
    })

    return formatDuration(duration, { format: ["minutes", "seconds"]});
}


export default DateTime;
