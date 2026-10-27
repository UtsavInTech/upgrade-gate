import { defineConfig } from 'vite';
// @ts-ignore JavaScript module is also the standalone sync CLI.
import { syncRuns } from './scripts/sync-runs.mjs';
import path from 'node:path';

export default defineConfig({server:{watch:{ignored:['**/public/runs/**']}},plugins:[{
  name:'saved-run-refresh',
  configureServer(server) {
    const results=path.resolve(server.config.root,'../results');
    let timer:ReturnType<typeof setTimeout>|undefined, running=false, again=false;
    async function refresh() {
      if(running){again=true;return;}
      running=true;
      try {await syncRuns({quiet:true});server.ws.send({type:'custom',event:'runs-updated'});}
      catch(error){server.config.logger.warn(`Run refresh: ${error}`);}
      finally{running=false;if(again){again=false;void refresh();}}
    }
    server.watcher.add(results);
    const changed=(file:string)=>{
      if(!file.startsWith(results+path.sep)||!['run.json','scores.jsonl','scores.before-rescore.jsonl','gate.json'].includes(path.basename(file)))return;
      clearTimeout(timer);timer=setTimeout(()=>void refresh(),900);
    };
    server.watcher.on('add',changed).on('change',changed).on('unlink',changed);
    server.httpServer?.once('close',()=>{clearTimeout(timer);server.watcher.off('add',changed).off('change',changed).off('unlink',changed);});
  }
}]});
