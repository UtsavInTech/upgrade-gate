import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import type { Comparison, Gate, Regression, Run, RunIndex, Task } from './types';
import './style.css';

const points = (n:number) => `${n > 0 ? '+' : n < 0 ? '−' : ''}${Math.abs(n*100).toFixed(1)}`;
const percent = (n:number) => `${(n*100).toFixed(1)}%`;
const money = (n:number) => `$${n.toFixed(4)}`;
const text = (value:unknown) => typeof value === 'string' ? value : JSON.stringify(value,null,2);
const pretty = (slice:string) => slice.replace('category=','').replace('lang=','language · ').replace('modality=','modality · ');
const matchSlice = (task:Task|undefined,slice:string|null) => !slice || !!task && String(task[slice.split('=')[0] as keyof Task]) === slice.split('=')[1];
async function fetchText(url:string,signal:AbortSignal) {
  const response = await fetch(url,{signal});
  if (!response.ok) throw new Error(`${url}: ${response.status}. Run npm run sync after generating the gate.`);
  return response.text();
}
const jsonl = <T,>(input:string):T[] => input.split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line));

function DeltaBar({ row, extent }: {row:Comparison;extent:number}) {
  const position = (value:number) => 50 + value/extent*48;
  return <svg viewBox="0 0 240 32" className="delta-bar" role="img" aria-label={`${points(row.delta)} points, confidence interval ${points(row.ci_low)} to ${points(row.ci_high)}`}>
    <line x1="120" x2="120" y1="0" y2="32" className="zero"/>
    <line x1={`${position(0)}%`} x2={`${position(row.delta)}%`} y1="16" y2="16" className="bar-fill"/>
    <line x1={`${position(row.ci_low)}%`} x2={`${position(row.ci_high)}%`} y1="16" y2="16" className="whisker"/>
    {[row.ci_low,row.ci_high].map((v,i) => <line key={i} x1={`${position(v)}%`} x2={`${position(v)}%`} y1="11" y2="21" className="whisker"/>)}
    <circle cx={`${position(row.delta)}%`} cy="16" r="4" className="delta-point"/>
  </svg>;
}

function Slices({gate,selected,onSelect}:{gate:Gate;selected:string|null;onSelect:(value:string|null)=>void}) {
  const rows = [...gate.slices].sort((a,b) => a.delta-b.delta);
  const extent = Math.max(.1,...rows.flatMap(r => [Math.abs(r.ci_low),Math.abs(r.ci_high)]))*1.08;
  return <section className="slice-panel" id="slices"><div className="section-heading"><div><span className="eyebrow">01 / Slice analysis</span><h2>Where it broke</h2></div><button className="text-button" disabled={!selected} onClick={()=>onSelect(null)}>Clear filter ↗</button></div>
    <div className="slice-legend"><span>Paired change · {percent(1-gate.thresholds.alpha)} CI</span><span>← Worse / Better →</span></div>
    {rows.length ? rows.map(row => <button key={row.slice} className={`slice-row ${row.verdict==='regression'?'regressed':''} ${selected===row.slice?'selected':''}`} aria-pressed={selected===row.slice} onClick={()=>onSelect(selected===row.slice?null:row.slice)}>
      <span className="slice-name">{pretty(row.slice)}<small>n={row.n} · Holm p={row.p_adjusted?.toPrecision(2)}{row.verdict==='regression'?' · regression':''}</small></span>
      <DeltaBar row={row} extent={extent}/><strong>{points(row.delta)}<small>pts</small></strong>
    </button>) : <p className="empty">No slices have the required 10 paired tasks.</p>}
    <p className="panel-note">Select a slice to inspect its majority regressions.</p>
  </section>;
}

function DiffText({value,other}:{value:string;other:string}) {
  // Highlight the changed middle span; common prefix/suffix tokens stay readable.
  const a = value.split(/(\s+|[{}:,])/), b = other.split(/(\s+|[{}:,])/);
  let start=0, end=0;
  while(start<a.length && start<b.length && a[start]===b[start]) start++;
  while(end<a.length-start && end<b.length-start && a[a.length-1-end]===b[b.length-1-end]) end++;
  return <pre>{a.slice(0,start).join('')}<mark>{a.slice(start,a.length-end).join('')}</mark>{end?a.slice(-end).join(''):''}</pre>;
}

function Cases({run,runPath,slice}:{run:Run;runPath:string;slice:string|null}) {
  const taskMap = useMemo(()=>new Map(run.tasks.map(t=>[t.id,t])),[run.tasks]);
  const cases = run.gate.regressions.filter(r=>matchSlice(taskMap.get(r.task_id),slice));
  const [chosen,setChosen]=useState(''), [repeat,setRepeat]=useState<number|null>(null);
  const item:Regression|undefined = cases.find(r=>r.task_id===chosen) ?? cases[0];
  const task = item && taskMap.get(item.task_id);
  const repeats = item ? [...new Set(run.responses.filter(r=>r.task_id===item.task_id).map(r=>r.repeat))].sort((a,b)=>a-b) : [];
  return <section className="case-panel" id="cases"><div className="section-heading"><div><span className="eyebrow">02 / Evidence explorer</span><h2>Inspect the regression</h2></div><span className="count">{cases.length} cases</span></div>
    {item && task ? <><div className="case-toolbar"><label className="sr-only" htmlFor="case-select">Regression case</label><select id="case-select" value={item.task_id} onChange={e=>setChosen(e.target.value)}>{cases.map(r=><option key={r.task_id} value={r.task_id}>{r.task_id} · {r.category} · {r.lang}</option>)}</select><span className="evidence-status">{item.evidence.confirmed?'Confirmed':'Majority disagreement'}</span></div>
    <div className="prompt-block"><div><span className="eyebrow">Prompt / {task.lang}</span><p>{task.prompt}</p><span className="muted">{item.evidence.cand_repeats-item.evidence.cand_passes}/{item.evidence.cand_repeats} candidate repeats failed · {item.evidence.base_passes}/{item.evidence.base_repeats} baseline passed</span></div>{task.attachments.map(asset=>/\.(png|jpe?g|gif|webp|svg)$/i.test(asset)?<a key={asset} href={`${runPath}/${asset}`} target="_blank" rel="noreferrer"><img src={`${runPath}/${asset}`} alt={`Source document for ${task.id}`} loading="lazy"/></a>:<a key={asset} href={`${runPath}/${asset}`} target="_blank" rel="noreferrer">Open attachment ↗</a>)}</div>
    <div className="reference"><span className="eyebrow">Expected reference</span><pre>{text(task.reference)}</pre></div>
    <div className="repeat-tabs" aria-label="Response repeats"><button aria-pressed={repeat===null} onClick={()=>setRepeat(null)}>All repeats</button>{repeats.map(r=><button key={r} aria-pressed={repeat===r} onClick={()=>setRepeat(r)}>Repeat {r+1}</button>)}</div>
    {(repeat===null?repeats:[repeat]).map(r=>{
      const old=run.responses.find(row=>row.task_id===task.id && row.candidate===run.gate.baseline && row.repeat===r);
      const next=run.responses.find(row=>row.task_id===task.id && row.candidate===run.gate.candidate && row.repeat===r);
      const oldScore=run.scores.find(row=>row.task_id===task.id && row.candidate===run.gate.baseline && row.repeat===r);
      const nextScore=run.scores.find(row=>row.task_id===task.id && row.candidate===run.gate.candidate && row.repeat===r);
      return <div className="repeat-pair" key={r}><div className="repeat-label">REPEAT {r+1}</div><div className="answer-grid">{[[old,oldScore,run.gate.baseline,next],[next,nextScore,run.gate.candidate,old]].map(([response,score,name,other],i)=>{
        const row=response as typeof old, result=score as typeof oldScore, counterpart=other as typeof old;
        return <article className={`answer ${result?.passed===false?'failed':''}`} key={i}><header><span>{name as string}</span><strong>{result?.passed===true?'PASS':result?.passed===false?'FAIL':'UNSCORED'}</strong></header>{row?.text!=null?<DiffText value={row.text} other={counterpart?.text??''}/>:<p className="empty">{row?.error??'No response recorded'}</p>}<footer>{row?`${row.usage.output_tokens??0} output tokens · ${row.latency_ms} ms · ${money(row.cost_usd)}`:'Missing repeat'}</footer></article>;
      })}</div></div>;
    })}</>:<div className="empty-state"><span>∅</span><h3>{slice?'No majority regressions in this slice.':'No majority regressions recorded.'}</h3><p>Choose another slice to continue inspecting the evidence.</p></div>}
  </section>;
}

function Cost({gate}:{gate:Gate}) {
  const old = gate.cost.usage?.[gate.baseline], next = gate.cost.usage?.[gate.candidate];
  const outputChange = old?.output_tokens ? (next.output_tokens/old.output_tokens-1)*100 : null;
  return <section className="cost-panel" id="cost"><div className="section-heading"><div><span className="eyebrow">03 / Efficiency</span><h2>The price of the upgrade</h2></div><span className="muted">{outputChange!==null?`${outputChange>0?'+':''}${outputChange.toFixed(1)}% output tokens`:'Output comparison unavailable'}</span></div>
    <div className="table-scroll"><table><thead><tr><th>Candidate</th><th>Input tokens</th><th>Output tokens</th><th>Reasoning tokens</th><th>Model + judge cost</th></tr></thead><tbody>{[[gate.baseline,old,gate.cost.base_usd],[gate.candidate,next,gate.cost.cand_usd]].map(([name,usage,cost])=>{const u=usage as typeof old;return <tr key={name as string}><td>{name as string}</td><td>{u?.input_tokens.toLocaleString()??'—'}</td><td>{u?.output_tokens.toLocaleString()??'—'}</td><td>{u?.reasoning_tokens.toLocaleString()??'—'}</td><td>{money(cost as number)}</td></tr>})}</tbody></table></div><p className="panel-note">Judging component: {money(gate.cost.judge_usd)}. Included in candidate totals.</p>
  </section>;
}

function App() {
  const [runs,setRuns]=useState<RunIndex[]>([]), [id,setId]=useState(''), [run,setRun]=useState<Run|null>(null), [error,setError]=useState(''), [loading,setLoading]=useState(true), [slice,setSlice]=useState<string|null>(null);
  useEffect(()=>{
    const controller=new AbortController();
    fetchText('/runs/index.json',controller.signal).then(value=>{const list=JSON.parse(value) as RunIndex[];setRuns(list);setId(list[0]?.id??'');if(!list.length){setError('No complete runs found. Generate gate.json, then run npm run sync.');setLoading(false)}}).catch(e=>{if(e.name!=='AbortError'){setError(e.message);setLoading(false)}});
    return ()=>controller.abort();
  },[]);
  useEffect(()=>{
    if(!id)return;
    const controller=new AbortController(), root=`/runs/${encodeURIComponent(id)}`;
    setLoading(true);setError('');setSlice(null);
    Promise.all(['gate.json','tasks.jsonl','responses.jsonl','scores.jsonl','run.json'].map(name=>fetchText(`${root}/${name}`,controller.signal)))
      .then(([gate,tasks,responses,scores,info])=>{setRun({gate:JSON.parse(gate),tasks:jsonl(tasks),responses:jsonl(responses),scores:jsonl(scores),info:JSON.parse(info)});setLoading(false)})
      .catch(e=>{if(e.name!=='AbortError'){setError(e.message);setLoading(false)}});
    return ()=>controller.abort();
  },[id]);
  const current=runs.find(r=>r.id===id), gate=run?.gate;
  return <><a className="skip-link" href="#main">Skip to evidence</a><header className="topbar"><a className="brand" href="#main"><span className="gate-icon" aria-hidden="true">Ⅱ</span>upgrade gate<span className="brand-dot">.</span></a><nav aria-label="Report sections"><a href="#slices">Slices</a><a href="#cases">Cases</a><a href="#cost">Cost</a></nav><label className="run-picker"><span>RUN</span><select aria-label="Choose run" value={id} onChange={e=>setId(e.target.value)}>{runs.map(r=><option key={r.id} value={r.id}>{r.label}{r.synthetic?' · demo':''}</option>)}</select></label></header>
    <main id="main">{loading?<div className="empty-state" role="status"><h1>Loading release evidence…</h1></div>:error?<div className="empty-state" role="alert"><h1>Couldn’t load this run</h1><p>{error}</p><button onClick={()=>window.location.reload()}>Retry</button></div>:gate && run?<>
      <div className="report-kicker"><span>MODEL UPGRADE / EVIDENCE REPORT</span><span>{gate.baseline} <span aria-hidden="true">→</span> {gate.candidate}</span></div>
      {current?.synthetic && <div className="synthetic-note">SYNTHETIC DEMO <span>Planted effects for demonstration. These are not measured model results.</span></div>}
      <section className={`verdict verdict-${gate.decision}`} aria-labelledby="verdict-title"><div><span className="eyebrow">Release decision</span><h1 id="verdict-title">{gate.decision.toUpperCase()}<span className="verdict-dot">.</span></h1></div><div className="verdict-explanation"><span className="eyebrow">{gate.decision==='no-go'?'The average hides the damage':gate.decision==='go'?'The upgrade clears the gate':'More evidence needed'}</span><p>{gate.reasons[0]}</p>{gate.reasons.length>1 && <details><summary>{gate.reasons.length-1} more decision reason(s)</summary>{gate.reasons.slice(1).map(reason=><p key={reason}>{reason}</p>)}</details>}<div className="decision-rule">Drop limit {points(-gate.thresholds.max_drop)} pts <span>/</span> α {gate.thresholds.alpha} <span>/</span> paired inference</div></div></section>
      <section className="metrics" aria-label="Headline numbers"><div><span className="eyebrow">Overall change</span><strong>{points(gate.overall.delta)}<small>pts</small></strong><span>{percent(1-gate.thresholds.alpha)} CI {points(gate.overall.ci_low)} to {points(gate.overall.ci_high)}</span></div><div><span className="eyebrow">Pass rate</span><strong>{percent(gate.overall.base_rate)}<small>→ {percent(gate.overall.cand_rate)}</small></strong><span>{gate.overall.n} paired tasks · {gate.overall.unpaired_tasks??0} excluded</span></div><div><span className="eyebrow">Cost change</span><strong>{gate.cost.delta_pct!==null?`${gate.cost.delta_pct>0?'+':''}${gate.cost.delta_pct.toFixed(1)}%`:'—'}</strong><span>{money(gate.cost.base_usd)} → {money(gate.cost.cand_usd)}</span></div><div><span className="eyebrow">Repeat noise floor</span><strong>{percent(gate.overall.noise_floor??0)}</strong><span>Repeat disagreements · {gate.overall.api_error_rows??0} null scores</span></div></section>
      <div className="evidence-grid"><Slices gate={gate} selected={slice} onSelect={setSlice}/><Cases key={id} run={run} runPath={`/runs/${encodeURIComponent(id)}`} slice={slice}/></div><Cost gate={gate}/>
      <details className="method-notes"><summary>How this decision was made</summary><p>One observation per task: majority vote across repeats, ties fail, null scores excluded. McNemar’s exact two-sided test measures discordance; Holm adjusts across all eligible slices. Pointwise bootstrap CIs resample paired tasks 10,000 times with seed 0. Slices need at least 10 pairs; the overall gate needs {gate.thresholds.min_n}. GO requires the lower CI to exceed the allowed drop and no significantly regressing slice. NO-GO follows a significant regressing slice or an overall upper CI below the drop limit. These are fixed-horizon intervals, unsuitable for repeated peeking. The separate sequential test uses anytime-valid mixture betting.</p><p>Noise floor: groups with disagreeing repeats divided by groups with at least two scored repeats. Exported tests require majority regression and supporting statistical evidence. Costs include model and judging charges. Review API errors and exclusions for selection bias.</p></details>
      <footer className="page-footer"><span>UPGRADE GATE / Trust the evidence.</span><span>{run.info.notes}</span><a href={`/runs/${encodeURIComponent(id)}/report.html`} target="_blank" rel="noreferrer">Standalone report ↗</a></footer>
    </>:null}</main></>;
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
