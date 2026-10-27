import type {Comparison} from './types';
export const points=(n:number,digits=1)=>`${n<0?'−':n>0?'+':''}${Math.abs(n*100).toFixed(digits)}`;
export const percent=(n:number)=>`${(n*100).toFixed(2)}%`;
export const money=(n:number|null|undefined)=>n==null?'n/a':`$${n.toFixed(4)}`;
export const text=(value:unknown)=>typeof value==='string'?value:JSON.stringify(value,null,2);
export const pretty=(slice:string)=>slice.replace('category=','').replace('lang=','language · ').replace('modality=','modality · ');
export const pvalue=(n:number|null)=>n==null?'n/a':n<.001?n.toExponential(2):n.toPrecision(3);
export function Help({children}:{children:React.ReactNode}){return <details className="help"><summary aria-label="How to read this">?</summary><div>{children}</div></details>}
export function DeltaBar({row,extent}:{row:Comparison;extent:number}){
 const pos=(value:number)=>50+value/extent*47;
 return <svg viewBox="0 0 240 32" className="delta-bar" role="img" aria-label={`${points(row.delta)} points; confidence interval ${points(row.ci_low)} to ${points(row.ci_high)}`}><line x1="120" x2="120" y1="0" y2="32" className="zero"/><line x1={`${pos(0)}%`} x2={`${pos(row.delta)}%`} y1="16" y2="16" className="bar-fill"/><line x1={`${pos(row.ci_low)}%`} x2={`${pos(row.ci_high)}%`} y1="16" y2="16" className="whisker"/>{[row.ci_low,row.ci_high].map((v,i)=><line key={i} x1={`${pos(v)}%`} x2={`${pos(v)}%`} y1="11" y2="21" className="whisker"/>)}<circle cx={`${pos(row.delta)}%`} cy="16" r="4" className="delta-point"/></svg>;
}
export function DiffText({value,other}:{value:string;other:string}){
 const a=value.split(/(\s+|[{}:,])/),b=other.split(/(\s+|[{}:,])/);let start=0,end=0;
 while(start<a.length&&start<b.length&&a[start]===b[start])start++;
 while(end<a.length-start&&end<b.length-start&&a[a.length-1-end]===b[b.length-1-end])end++;
 return <pre>{a.slice(0,start).join('')}<mark>{a.slice(start,a.length-end).join('')}</mark>{end?a.slice(-end).join(''):''}</pre>;
}
