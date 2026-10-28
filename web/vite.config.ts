import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import fs from "node:fs";
import { spawn, type ChildProcess } from "node:child_process";
import path from "node:path";

const REPO = path.resolve(__dirname, "..");

// Dev-only endpoint for the recording page: POST /api/record?speaker=<id>&clip=<clip_id> with a WAV body.
// Saves to data/audio-real/<speaker>/<clip>.wav and appends data/audio-real/manifest.jsonl.
function recorder(): Plugin {
  const allowed = new Set<string>(
    ["record.json", "record-corrections.json"].flatMap((f) =>
      JSON.parse(fs.readFileSync(path.join(__dirname, "public/data", f), "utf8")).map(
        (r: { clip_id: string }) => r.clip_id,
      ),
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
      // Label audit: POST /api/audit?labeler=<id> {id, label, note} appends to data/audit/labels-<id>.jsonl;
      // GET returns the latest label per item.
      server.middlewares.use("/api/audit", (req, res) => {
        const url = new URL(req.url ?? "", "http://x");
        const labeler = (url.searchParams.get("labeler") ?? "").toLowerCase();
        if (!/^[a-z0-9-]{1,32}$/.test(labeler)) {
          res.statusCode = 400;
          res.end("bad labeler");
          return;
        }
        const file = path.join(REPO, "data", "audit", `labels-${labeler}.jsonl`);
        if (req.method === "GET") {
          const out: Record<string, string> = {};
          if (fs.existsSync(file)) {
            for (const line of fs.readFileSync(file, "utf8").split("\n")) {
              if (!line.trim()) continue;
              const r = JSON.parse(line);
              out[r.id] = r.label;
            }
          }
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify(out));
          return;
        }
        const chunks: Buffer[] = [];
        req.on("data", (c: Buffer) => chunks.push(c));
        req.on("end", () => {
          try {
            const r = JSON.parse(Buffer.concat(chunks).toString("utf8"));
            const ok = ["correct", "abstain", "blank", "wrong", "unsure"];
            if (!/^a\d{2}$/.test(r.id) || !ok.includes(r.label)) throw new Error("bad label");
            fs.mkdirSync(path.dirname(file), { recursive: true });
            fs.appendFileSync(
              file,
              JSON.stringify({
                id: r.id,
                label: r.label,
                note: String(r.note ?? "").slice(0, 300),
                ts: new Date().toISOString(),
              }) + "\n",
            );
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ ok: true }));
          } catch {
            res.statusCode = 400;
            res.end("bad request");
          }
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

// Starts the VoiceOrder API (voiceorder/server.py, port 5192) alongside the dev server, so one
// `npm run dev` runs everything. /api/voiceorder is proxied to it below.
function voiceOrderApi(): Plugin {
  let child: ChildProcess | null = null;
  return {
    name: "voiceorder-api",
    configureServer(server) {
      const py = fs.existsSync(path.join(REPO, ".venv/bin/python"))
        ? path.join(REPO, ".venv/bin/python")
        : "python3";
      child = spawn(py, ["-m", "voiceorder.server"], {
        cwd: REPO,
        env: { ...process.env, PYTHONPATH: REPO },
        stdio: ["ignore", "inherit", "inherit"],
      });
      const stop = () => child && !child.killed && child.kill();
      server.httpServer?.on("close", stop);
      process.on("exit", stop);
    },
  };
}

export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss(), recorder(), voiceOrderApi()],
  server: { proxy: { "/api/voiceorder": "http://127.0.0.1:5192" } },
});
