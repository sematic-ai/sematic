import Box from "@mui/material/Box";
import { Run } from "../Models";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import docco from "react-syntax-highlighter/dist/esm/styles/hljs/docco";
import python from "react-syntax-highlighter/dist/esm/languages/hljs/python";

SyntaxHighlighter.registerLanguage("python", python);

function SourceCode(props: { run: Run }) {
  let run = props.run;

  return (
    <Box key={run.calculator_path} sx={{ marginTop: 2 }}>
      <SyntaxHighlighter
        language="python"
        style={docco}
        showLineNumbers
        customStyle={{ fontSize: 12 }}
      >
        {run.source_code}
      </SyntaxHighlighter>
    </Box>
  );
}

export default SourceCode;
