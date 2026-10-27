export interface Comparison { slice:string; n:number; base_rate:number; cand_rate:number; delta:number; ci_low:number; ci_high:number; p_value:number; p_adjusted:number|null; verdict:string; noise_floor?:number; unpaired_tasks?:number; api_error_rows?:number }
export interface Regression { task_id:string; category:string; lang:string; reference:unknown; base_text:string; cand_text:string; evidence:{ confirmed?:boolean; base_passes:number; base_repeats:number; cand_passes:number; cand_repeats:number; failure_consistency:number } }
export interface Usage { input_tokens:number; output_tokens:number; reasoning_tokens:number }
export interface Gate { run_id:string; baseline:string; candidate:string; decision:'go'|'no-go'|'inconclusive'; reasons:string[]; overall:Comparison; slices:Comparison[]; regressions:Regression[]; cost:{base_usd:number; cand_usd:number; delta_pct:number|null; judge_usd:number; usage:Record<string,Usage>}; thresholds:{ max_drop:number; alpha:number; min_n:number } }
export interface Task {id:string; prompt:string; reference:unknown; category:string; lang:string; modality:string; attachments:string[]}
export interface Response {task_id:string; candidate:string; repeat:number; text:string|null; error:string|null; usage:Usage; cost_usd:number; latency_ms:number}
export interface Score {task_id:string; candidate:string; repeat:number; passed:boolean|null}
export interface RunIndex {id:string; run_id:string; label:string; decision:string; created_utc:string; synthetic:boolean}
export interface Run {gate:Gate; tasks:Task[]; responses:Response[]; scores:Score[]; info:{notes:string; repeats:number}}
