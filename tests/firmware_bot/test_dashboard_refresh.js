const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(require('path').join(__dirname,'../../vendor/MeshCore/examples/companion_radio/RepeaterMonitorPage.html'),'utf8');
const api=html.slice(html.indexOf('async function api('),html.indexOf('\nfunction ',html.indexOf('async function api(')));
const refresh=html.slice(html.indexOf('let refreshInFlight=false;'),html.indexOf('\n',html.indexOf('async function refresh(')));
(async()=>{
 let timeout,cleared=0;
 const ctx=vm.createContext({AbortController,canManage:()=>true,setTimeout:fn=>(timeout=fn,1),clearTimeout:()=>cleared++,fetch:(url,options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(Object.assign(new Error(),{name:'AbortError'}))))});
 // Extract only api, excluding following declarations.
 vm.runInContext(api.slice(0,api.indexOf('\n}')+2),ctx);
 const pending=ctx.api('/api/state');timeout();await assert.rejects(pending,/timed out/);assert.equal(cleared,1);
 ctx.fetch=async()=>({ok:true,json:async()=>({ok:true})});assert.equal((await ctx.api('/api/state')).ok,true);assert.equal(cleared,2);
 ctx.fetch=async()=>({ok:false,status:503,text:async()=> 'Path lookup in progress'});
 await assert.rejects(ctx.api('/api/state'),e=>e.lookupBusy===true);
 await assert.rejects(ctx.api('/api/list'),e=>e.lookupBusy===false);
 let requests=0,rejectRequest;
 const rctx=vm.createContext({state:null,canManage:()=>true,api:()=>{requests++;return new Promise((resolve,reject)=>rejectRequest=reject);},notice:()=>{},$:()=>({})});
 vm.runInContext(refresh,rctx);
 const first=rctx.refresh();await rctx.refresh();assert.equal(requests,1);
 rejectRequest(new Error('offline'));await first;
 const retry=rctx.refresh();assert.equal(requests,2);rejectRequest(new Error('offline'));await retry;
 const held={repeaters:[]};rctx.state=held;let noticeText='';rctx.notice=t=>noticeText=t;
 rctx.api=async()=>{throw Object.assign(new Error('Path lookup in progress'),{lookupBusy:true});};
 rctx.$=()=>{throw Error('busy refresh must not disable controls');};
 await rctx.refresh();assert.strictEqual(rctx.state,held);assert(noticeText.includes('resume automatically'));
 console.log('PASS: dashboard read timeout, timer cleanup, no overlapping refreshes and retry after failure');
})().catch(e=>{console.error(e);process.exitCode=1;});
