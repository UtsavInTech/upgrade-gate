/** Copy only complete runs and their referenced assets. No backend required. */
import { mkdir, readdir, readFile, writeFile, cp, realpath, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const repo = path.resolve(fileURLToPath(new URL('../../', import.meta.url)));
const output = path.join(repo, 'ui/public/runs');
const results = path.join(repo, 'results');
const dirs = (await readdir(results, { withFileTypes: true }).catch(() => [])).filter(d => d.isDirectory()).map(d => path.join(results, d.name));
dirs.push(path.join(repo, 'tests/fixtures/run_demo'));
await mkdir(output, { recursive: true });
const index = [], seen = new Set();
for (const source of dirs) {
  let run, gate;
  try {
    run = JSON.parse(await readFile(path.join(source, 'run.json'), 'utf8'));
    gate = JSON.parse(await readFile(path.join(source, 'gate.json'), 'utf8'));
  } catch { console.warn(`Skipping incomplete run: ${path.relative(repo, source)} (generate gate.json first)`); continue; }
  // Directory names are not taken from untrusted run IDs.
  const id = path.basename(source);
  if (seen.has(id)) throw new Error(`Duplicate run directory: ${id}`);
  seen.add(id);
  const dest = path.join(output, id);
  await rm(dest, { recursive: true, force: true });
  await mkdir(path.join(dest, 'assets'), { recursive: true });
  for (const name of ['gate.json','run.json','responses.jsonl','scores.jsonl']) {
    await cp(path.join(source, name), path.join(dest, name));
  }
  const tasks = (await readFile(path.join(source, 'tasks.jsonl'), 'utf8')).split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line));
  for (const task of tasks) {
    task.attachments = await Promise.all((task.attachments ?? []).map(async attachment => {
      const sourceAsset = await realpath(path.resolve(repo, attachment));
      if (!sourceAsset.startsWith(repo + path.sep)) throw new Error(`Asset is outside repository: ${attachment}`);
      const hash = createHash('sha256').update(attachment).digest('hex').slice(0, 12);
      const local = `assets/${hash}-${path.basename(sourceAsset)}`;
      await cp(sourceAsset, path.join(dest, local));
      return local;
    }));
  }
  await writeFile(path.join(dest, 'tasks.jsonl'), tasks.map(t => JSON.stringify(t)).join('\n')+'\n');
  for (const name of ['report.html','report.md','exports']) {
    await cp(path.join(source, name), path.join(dest, name), { recursive: true }).catch(error => { if (error.code !== 'ENOENT') throw error; });
  }
  index.push({ id, run_id: run.run_id, label: run.run_id, decision: gate.decision, created_utc: run.created_utc, synthetic: run.packs?.includes('synthetic-demo') ?? false });
}
index.sort((a,b) => b.created_utc.localeCompare(a.created_utc));
await writeFile(path.join(output, 'index.json'), JSON.stringify(index, null, 2)+'\n');
console.log(`Synced ${index.length} runs to ui/public/runs/`);
