import Box from "@mui/material/Box";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import docco from "react-syntax-highlighter/dist/esm/styles/hljs/docco";
import python from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import { Run } from "src/Models";

SyntaxHighlighter.registerLanguage("python", python);

interface SourceCodeProps {
    run: Run;
    className?: string;
}

function SourceCode(props: SourceCodeProps) {
    const { run, className } = props;
  
    return (
        <Box key={run.function_path} sx={{ marginTop: 2 }} className={className}>
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
