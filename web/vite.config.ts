import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import fs from "node:fs";
import path from "node:path";

const REPO = path.resolve(__dirname, "..");

// Dev-only endpoint for the recording page: POST /api/record?speaker=<id>&clip=<clip_id> with a WAV body.
// Saves to data/audio-real/<speaker>/<clip>.wav and appends data/audio-real/manifest.jsonl.
function recorder(): Plugin {
  const allowed = new Set<string>(
    JSON.parse(fs.readFileSync(path.join(__dirname, "public/data/record.json"), "utf8")).map(
      (r: { clip_id: string }) => r.clip_id,
    ),
  );
  return {
    name: "upgrade-gate-recorder",
    configureServer(server) {
      server.middlewares.use("/api/record", (req, res) => {
        const url = new URL(req.url ?? "", "http://x");
        const speaker = (url.searchParams.get("speaker") ?? "").toLowerCase();
        const clip = url.searchParams.get("clip") ?? "";
        if (req.method !== "POST" || !/^[a-z0-9-]{1,32}$/.test(speaker) || !allowed.has(clip)) {
          res.statusCode = 400;
          res.end("bad request");
          return;
        }
        const chunks: Buffer[] = [];
        req.on("data", (c: Buffer) => chunks.push(c));
        req.on("end", () => {
          const body = Buffer.concat(chunks);
          if (body.length < 44 || body.length > 10_000_000 || body.toString("ascii", 0, 4) !== "RIFF") {
            res.statusCode = 400;
            res.end("not a wav");
            return;
          }
          const dir = path.join(REPO, "data", "audio-real", speaker);
          fs.mkdirSync(dir, { recursive: true });
          fs.writeFileSync(path.join(dir, `${clip}.wav`), body);
          fs.appendFileSync(
            path.join(REPO, "data", "audio-real", "manifest.jsonl"),
            JSON.stringify({
              speaker,
              clip_id: clip,
              wav: `data/audio-real/${speaker}/${clip}.wav`,
              ts: new Date().toISOString(),
            }) + "\n",
          );
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ ok: true }));
        });
      });
      server.middlewares.use("/api/recorded", (req, res) => {
        const url = new URL(req.url ?? "", "http://x");
        const speaker = (url.searchParams.get("speaker") ?? "").toLowerCase();
        const dir = path.join(REPO, "data", "audio-real", speaker);
        const done =
          /^[a-z0-9-]{1,32}$/.test(speaker) && fs.existsSync(dir)
            ? fs
                .readdirSync(dir)
                .filter((f) => f.endsWith(".wav"))
                .map((f) => f.slice(0, -4))
            : [];
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify(done));
      });
    },
  };
}

export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss(), recorder()],
});
