export interface Comparison {slice:string;n:number;base_rate:number;cand_rate:number;delta:number;ci_low:number;ci_high:number;p_value:number;p_adjusted:number|null;verdict:string;noise_floor?:number;unpaired_tasks?:number;api_error_rows?:number}
export interface Cell extends Comparison {category:string;lang:string;modality:string;task_ids:string[]}
export interface Regression {task_id:string;category:string;lang:string;modality:string;reference:unknown;evidence:{confirmed:boolean;base_passes:number;base_repeats:number;cand_passes:number;cand_repeats:number;failure_consistency:number;supporting_slices:string[]}}
export interface Metric {available:boolean;field:'passed'|'strict_passed';overall:Comparison;slices:Comparison[];cells:Cell[];regressions:Regression[];raw:Record<string,{passed:number;scored:number;rate:number|null}>;decision:'go'|'no-go'|'inconclusive';reason:string}
export interface RescoreExample {task_id:string;candidate:string;repeat:number;before:boolean|null;after:boolean|null;strict:boolean|null;text:string|null;detail:string;before_detail:string}
export interface Rescore {before:Comparison;after:Comparison;changed_rows:number;common_tasks:number;examples:RescoreExample[];source_before:string;source_after:string}
export interface Usage {input_tokens:number;output_tokens:number;reasoning_tokens:number;cached_tokens?:number}
export interface CostRow {candidate:string;model_id:string;mode:string;calls:number;unique_tasks:number;model_usd:number;judge_usd:number;total_usd:number;per_1000_tasks:number|null;usage:Usage;estimated_per_1000:{standard?:number|null;contributor?:number|null}}
export interface CandidateView {baseline:string;candidate:string;content:Metric;strict:Metric;rescore:Rescore|null;costs:CostRow[]}
export interface Analysis {run_id:string;synthetic:boolean;thresholds:{alpha:number;max_drop:number;min_n:number};comparisons:CandidateView[];total_calls:number;total_run_usd:number;notes:string;source:string;methods:{title:string;body:string}[]}
export interface Task {id:string;prompt:string;reference:unknown;category:string;lang:string;modality:string;attachments:string[];scorer:Record<string,unknown>}
export interface Response {task_id:string;candidate:string;repeat:number;text:string|null;error:string|null;usage:Usage;cost_usd:number;latency_ms:number}
export interface Score {task_id:string;candidate:string;repeat:number;passed:boolean|null;strict_passed?:boolean|null;detail:string;method:string}
export interface RunIndex {id:string;run_id:string;label:string;created_utc:string;synthetic:boolean;status:'ready'|'pending';revision:string;has_report:boolean;message?:string}
export interface Run {analysis:Analysis;tasks:Task[];responses:Response[];scores:Score[];info:{notes:string;repeats:number}}
export type ScoreMode='content'|'strict';
