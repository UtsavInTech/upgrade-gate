import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {syncRuns} from './sync-runs.mjs';

async function makeRun(repo,id) {
 const root=path.join(repo,'results',id);await mkdir(root,{recursive:true});
 await writeFile(path.join(root,'run.json'),JSON.stringify({run_id:id,created_utc:'2026-10-27T00:00:00Z',baseline:'old',candidates:[{name:'old',model_id:'muse-spark-1.2'},{name:'new',model_id:'muse-spark-1.3'}],packs:['test']}));
 const tasks=Array.from({length:30},(_,i)=>({id:String(i),category:'math',lang:'en',modality:'text',prompt:'Test task',reference:'4',scorer:{type:'exact_cs'},attachments:[]}));
 const responses=tasks.flatMap(task=>['old','new'].map(candidate=>({task_id:task.id,candidate,repeat:0,text:'4',usage:{input_tokens:2,output_tokens:1},cost_usd:0,latency_ms:1})));
 const scores=responses.map(row=>({task_id:row.task_id,candidate:row.candidate,repeat:0,passed:true,strict_passed:true,cost_usd:0}));
 for(const [file,rows] of [['tasks',tasks],['responses',responses],['scores',scores]])await writeFile(path.join(root,`${file}.jsonl`),rows.map(row=>JSON.stringify(row)).join('\n')+'\n');
 return root;
}

test('discovers new runs without gate files and preserves complete snapshots during writes',async()=>{
 const repo=await mkdtemp(path.join(tmpdir(),'upgrade-gate-ui-'));
 try {
  const output=path.join(repo,'public');const first=await makeRun(repo,'e1');
  let index=await syncRuns({repo,output,quiet:true});assert.equal(index.length,1);assert.equal(index[0].status,'ready');
  const analysis=JSON.parse(await readFile(path.join(output,'e1','analysis.json'),'utf8'));
  assert.equal(analysis.comparisons[0].strict.overall.delta,0);
  await makeRun(repo,'e4');index=await syncRuns({repo,output,quiet:true});assert.equal(index.length,2);
  await writeFile(path.join(first,'scores.jsonl'),'{"partially written":');
  index=await syncRuns({repo,output,quiet:true});assert.equal(index.find(r=>r.id==='e1').status,'ready');
  assert.match(index.find(r=>r.id==='e1').message,/last complete snapshot/);
  assert.deepEqual(JSON.parse(await readFile(path.join(output,'e1','analysis.json'),'utf8')),analysis);
  await mkdir(path.join(repo,'results','pending'));await writeFile(path.join(repo,'results','pending','run.json'),JSON.stringify({run_id:'pending',created_utc:'2026-10-27T01:00:00Z'}));
  index=await syncRuns({repo,output,quiet:true});assert.equal(index.find(r=>r.id==='pending').status,'pending');
 }finally{await rm(repo,{recursive:true,force:true})}
});
