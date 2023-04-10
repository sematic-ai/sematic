import { useTheme } from "@mui/material/styles";
import Typography from "@mui/material/Typography";
import {format, parseJSON} from "date-fns";

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

export default DateTime;
