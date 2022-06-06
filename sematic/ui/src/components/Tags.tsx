import IconButton from "@mui/material/IconButton";
import Chip, { ChipProps } from "@mui/material/Chip";
import AddIcon from "@mui/icons-material/Add";
import { Typography } from "@mui/material";

function Tags(props: { tags: Array<string>; chipProps?: ChipProps }) {
  return (
    <>
      {/*
      <Typography variant="overline" color="GrayText">
        Tags:
      </Typography>
      */}
      {props.tags.map((tag) => (
        <Chip
          label={tag}
          color="primary"
          size="small"
          variant="outlined"
          key={tag}
          sx={{ marginRight: 1 }}
          {...props.chipProps}
        />
      ))}
      {/*
      <IconButton color="secondary">
        <AddIcon />
      </IconButton>
      */}
    </>
  );
}

export default Tags;
