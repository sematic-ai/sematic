import { Stack, Box, Typography, useTheme } from "@mui/material";

const messages = [
  {
    author: "alice@acme.ai",
    message:
      "The distribution looks skewed. Can you try with a greater threshold?",
    time: "Yesterday at 2:53pm",
  },
  {
    author: "bob@acme.ai",
    message:
      "Sure, let me take a look, the sampling may be using last week's snapshot too.",
    time: "Yesterday at 4:31pm",
  },
];

function Note(props: {
  message: { author: string; message: string; time: string };
}) {
  const { author, message, time } = props.message;
  const theme = useTheme();

  return (
    <Box
      sx={{
        borderTop: 1,
        borderColor: theme.palette.grey[200],
        color: theme.palette.grey[800],
        px: 2,
        py: 1,
      }}
      key={Math.random().toString()}
    >
      <Typography sx={{ fontSize: "small", color: theme.palette.grey[500] }}>
        {author}:
      </Typography>
      <Box sx={{ my: 4 }}>
        <Typography fontSize="small">{message}</Typography>
      </Box>
      <Typography
        sx={{
          fontSize: "small",
          color: theme.palette.grey[500],
          textAlign: "right",
        }}
      >
        {time}
      </Typography>
    </Box>
  );
}

export default function Notes(props: { calculatorPath: string }) {
  const theme = useTheme();
  return (
    <Box sx={{ display: "grid", gridTemplateRows: "1fr auto" }}>
      <Box sx={{ gridRow: 1 }}></Box>

      <Stack sx={{ gridRow: 2 }}>
        {messages.map((message) => (
          <Note message={message} />
        ))}
      </Stack>
    </Box>
  );
}
