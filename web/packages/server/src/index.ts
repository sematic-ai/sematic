import cors from "cors";
import express from "express";
import { join } from "path";

const PORT = 3000;

const app = express();
app.use(cors());

// Serve static resources from the "public" folder (ex: when there are images to display)
app.use(express.static(join(__dirname, "../../app/public")));

// Serve the HTML page
app.get("*", (req: any, res: any) => {
  res.sendFile(join(__dirname, "../../app/public", "index.html"));
});

app.listen(PORT, () => {
  console.log(`Glows server listening at http://localhost:${PORT}`);
});