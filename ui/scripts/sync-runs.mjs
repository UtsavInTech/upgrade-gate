/** Build static presentation data from local runs. Never calls a model. */
import { mkdir, readdir, readFile, writeFile, cp, realpath, rm, rename, stat } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const defaultRepo = path.resolve(fileURLToPath(new URL('../../', import.meta.url)));
export async function syncRuns({repo=defaultRepo, output=path.join(repo,'ui/public/runs'), quiet=false}={}) {
  const results=path.join(repo,'results');
  const directories=(await readdir(results,{withFileTypes:true}).catch(()=>[])).filter(d=>d.isDirectory()).map(d=>path.join(results,d.name));
  directories.push(path.join(repo,'tests/fixtures/run_demo'));
  await mkdir(output,{recursive:true});
  const previous=await readFile(path.join(output,'index.json'),'utf8').then(JSON.parse,()=>[]);
  const sourceVersion=(await Promise.all(['upgrade_gate/report.py','upgrade_gate/stats.py','upgrade_gate/pricing.py','ui/scripts/sync-runs.mjs'].map(async file=>{const s=await stat(path.join(defaultRepo,file));return `${s.size}:${s.mtimeMs}`;}))).join('|');
  const index=[],seen=new Set();
  for(const source of directories) {
    const id=path.basename(source);
    if(seen.has(id)) throw new Error(`Duplicate run directory: ${id}`);
    seen.add(id);
    let run;
    try { run=JSON.parse(await readFile(path.join(source,'run.json'),'utf8')); }
    catch {continue;}
    const metadata={id,run_id:run.run_id,label:run.run_id,created_utc:run.created_utc,synthetic:run.packs?.includes('synthetic-demo')??false};
    const dest=path.join(output,id), staging=path.join(output,`.${id}-sync`);
    try {
      // A partially written JSONL line is retried at the next watched change.
      for(const name of ['tasks.jsonl','responses.jsonl','scores.jsonl']) {
        const input=await readFile(path.join(source,name),'utf8');
        for(const line of input.split(/\r?\n/).filter(Boolean)) JSON.parse(line);
        if(!input.trim()) throw new Error(`${name} has no records yet`);
      }
      const revision=sourceVersion+(await Promise.all(['run.json','tasks.jsonl','responses.jsonl','scores.jsonl','scores.before-rescore.jsonl','gate.json','report.html'].map(async name=>{
        const s=await stat(path.join(source,name)).catch(()=>null);return s?`${name}:${s.size}:${s.mtimeMs}`:'';
      }))).join('|');
      const fingerprint=createHash('sha256').update(revision).digest('hex').slice(0,16);
      const prior=previous.find(r=>r.id===id&&r.revision===fingerprint&&r.status==='ready');
      if(prior&&await stat(path.join(dest,'analysis.json')).then(()=>true,()=>false)){index.push({...prior,...metadata});continue;}
      const analysis=JSON.parse(await analyze(source,repo));
      if(!analysis.comparisons.length||!analysis.comparisons.some(c=>c.content.available)) throw new Error('Waiting for paired scored candidates');
      await rm(staging,{recursive:true,force:true});
      await mkdir(path.join(staging,'assets'),{recursive:true});
      for(const name of ['run.json','responses.jsonl','scores.jsonl']) await cp(path.join(source,name),path.join(staging,name));
      for(const name of ['gate.json','scores.before-rescore.jsonl','report.html','report.md','exports']) {
        await cp(path.join(source,name),path.join(staging,name),{recursive:true}).catch(error=>{if(error.code!=='ENOENT') throw error;});
      }
      const tasks=(await readFile(path.join(source,'tasks.jsonl'),'utf8')).split(/\r?\n/).filter(Boolean).map(line=>JSON.parse(line));
      for(const task of tasks) {
        task.attachments=await Promise.all((task.attachments??[]).map(async attachment=>{
          const asset=await realpath(path.resolve(repo,attachment));
          const root=await realpath(repo);
          if(!asset.startsWith(root+path.sep)) throw new Error(`Asset is outside repository: ${attachment}`);
          const local=`assets/${createHash('sha256').update(attachment).digest('hex').slice(0,12)}-${path.basename(asset)}`;
          await cp(asset,path.join(staging,local));return local;
        }));
      }
      await writeFile(path.join(staging,'tasks.jsonl'),tasks.map(t=>JSON.stringify(t)).join('\n')+'\n');
      await writeFile(path.join(staging,'analysis.json'),JSON.stringify(analysis));
      // Copy-on-complete keeps clients from observing half-written analysis.
      await rm(dest,{recursive:true,force:true});await rename(staging,dest);
      const hasReport=await stat(path.join(dest,'report.html')).then(()=>true,()=>false);
      index.push({...metadata,status:'ready',decision:analysis.comparisons[0].content.decision,revision:fingerprint,has_report:hasReport});
    } catch(error) {
      await rm(staging,{recursive:true,force:true});
      const prior=await readFile(path.join(dest,'analysis.json'),'utf8').then(()=>true,()=>false);
      if(!quiet) console.warn(`${id}: ${error.message}`);
      index.push({...metadata,status:prior?'ready':'pending',revision:'pending',has_report:false,message:prior?'Showing last complete snapshot; new data is being written.':'Waiting for complete local scores and responses.'});
    }
  }
  for(const entry of await readdir(output,{withFileTypes:true})){if(entry.isDirectory()&&!entry.name.startsWith('.')&&!seen.has(entry.name))await rm(path.join(output,entry.name),{recursive:true,force:true});}
  index.sort((a,b)=>Number(a.synthetic)-Number(b.synthetic)||b.created_utc.localeCompare(a.created_utc));
  const temporary=path.join(output,'.index-next.json');
  await writeFile(temporary,JSON.stringify(index,null,2)+'\n');await rename(temporary,path.join(output,'index.json'));
  if(!quiet) console.log(`Synced ${index.filter(r=>r.status==='ready').length} ready runs; ${index.filter(r=>r.status==='pending').length} pending.`);
  return index;
}
function analyze(source,repo) {
  return new Promise((resolve,reject)=>{
    const python=process.env.UPGRADE_GATE_PYTHON??path.join(defaultRepo,'.venv/bin/python');
    const child=spawn(python,['-m','upgrade_gate.report',source,'--analysis'],{cwd:repo,env:{...process.env,PYTHONPATH:defaultRepo}});
    let output='',error='';
    child.stdout.on('data',data=>output+=data);child.stderr.on('data',data=>error+=data);
    child.on('error',reject);child.on('close',code=>code===0?resolve(output):reject(new Error(error||`Analysis exited ${code}`)));
  });
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) await syncRuns();
