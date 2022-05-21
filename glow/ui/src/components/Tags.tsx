import Chip from "@mui/material/Chip";

function Tags(props: { tags: Array<string> }) {
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
        />
      ))}
    </>
  );
}

export default Tags;
