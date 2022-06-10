import Chip, { ChipProps } from "@mui/material/Chip";

function Tags(props: { tags: Array<string>; chipProps?: ChipProps }) {
  return (
    <>
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
    </>
  );
}

export default Tags;
