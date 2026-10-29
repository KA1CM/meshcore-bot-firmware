const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'../../vendor/MeshCore/examples/companion_radio');
const html=fs.readFileSync(path.join(root,'RepeaterMonitorPage.html'),'utf8');
const renderer=html.slice(html.indexOf('function renderScopedRepeaters(){'),html.indexOf('function renderNeighbors()'));
function node(tag,text,cls){return {tag,textContent:text,className:cls,children:[],append(...items){this.children.push(...items);},replaceChildren(){this.children=[];}};}
const ids={};const $=id=>ids[id]||(ids[id]=node('div'));
const state={ctFfcRepeaters:{today:20000,storageReady:true,entries:[
 {hash:'abcd',name:'Full Repeater Name With All Words',ambiguous:false,lastDay:19998},
 {hash:'1234',name:'',ambiguous:true,lastDay:20000}
]}};
const context={state,$,node,document:{createTextNode:text=>node('#text',text)},commandDayLabel:day=>'day '+day};
vm.createContext(context);vm.runInContext(renderer+'\nrenderScopedRepeaters();',context);
assert.strictEqual($('ctffcrows').children.length,2);
assert.strictEqual($('ctffcrows').children[0].children[0].children[0].textContent,'1234.');
assert.strictEqual($('ctffcrows').children[1].children[0].children[2].textContent,'Full Repeater Name With All Words');
assert(html.includes('grid-template-columns:repeat(3,minmax(0,1fr))'));
assert(!html.includes('ctffc-scroll'));
assert(!html.includes('<table id="ctffctable"'));
state.ctFfcRepeaters.entries=[];vm.runInContext('renderScopedRepeaters();',context);
assert.strictEqual($('ctffctable').hidden,true);
console.log('PASS: three-column layout, no internal scroll, full names, hash-first labels, sorting and empty list');
