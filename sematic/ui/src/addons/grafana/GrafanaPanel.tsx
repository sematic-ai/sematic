import { OpenInNew } from "@mui/icons-material";
import { Box, Button } from "@mui/material";
import { useContext, useMemo } from "react";
import { EnvContext } from "../..";
import { Run } from "../../Models";

export default function GrafanaPanel(props: { run: Run }) {
  const { run } = props;
  const env: Map<string, string> = useContext(EnvContext);
  const grafanaPanelUrlSettings = env.get("GRAFANA_PANEL_URL");
  const iframeTitle = useMemo(() => `Grafana panel for run ${run.id}`, [run]);

  // in principle this should never show because the tab shouldn't show up if Grafana is off.
  if (!grafanaPanelUrlSettings) {
    return <p>Grafana not configured.</p>;
  }

  const grafanaPanelUrl: URL = new URL(grafanaPanelUrlSettings);

  const runEnd: Date | null = run.failed_at || run.resolved_at || run.ended_at;

  const from: string = new Date(run.created_at).getTime().toString();
  const to: string = (
    (runEnd ? new Date(runEnd) : new Date()).getTime() + 10000
  ).toString();

  grafanaPanelUrl.searchParams.set("from", from);
  grafanaPanelUrl.searchParams.set("to", to);
  grafanaPanelUrl.searchParams.set("var-container", "sematic-worker-" + run.id);
  grafanaPanelUrl.searchParams.set("theme", "light");


  return (
    <>
      <Box sx={{ my: 10 }}>
        <Button
          variant="contained"
          href={grafanaPanelUrl.toString()}
          endIcon={<OpenInNew />}
        >
          Grafana Panel
        </Button>
      </Box>
      <Box>
        <iframe
          title={iframeTitle}
          src={grafanaPanelUrl.toString()}
          style={{ border: 0, width: "100%", height: 1000 }}
        ></iframe>
      </Box>
    </>
  );
}
