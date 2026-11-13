const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const elements=new Map();
function el(selector){if(!elements.has(selector))elements.set(selector,{textContent:'',innerHTML:'',value:'',hidden:false,open:false,disabled:false,checked:false,style:{},classList:{toggle(){}},addEventListener(){},insertAdjacentHTML(){},showModal(){this.open=true;},close(){this.open=false;},click(){this.onclick?.();}});return elements.get(selector);}
let rows=[],resolveImport,uploadStarted;
const started=new Promise(resolve=>uploadStarted=resolve);
const timers=[];
const context=vm.createContext({console,AbortController,setTimeout,clearTimeout,setInterval:fn=>timers.push(fn),confirm:()=>true,
 document:{querySelector:el,querySelectorAll:()=>[]},
 FileReader:class{readAsDataURL(){this.result='data:image/png;base64,AAAA';queueMicrotask(()=>this.onload());}},
 fetch:async(path)=>{if(path==='/api/import'){uploadStarted();return await new Promise(resolve=>resolveImport=()=>resolve({ok:true,json:async()=>({id:1,duplicate:false})}));}return {ok:true,json:async()=>path==='/api/health'?{ready:true,provider:'tokenhub'}:rows};}
});
const read=name=>fs.readFileSync(require('node:path').join(__dirname,'../static',name),'utf8');
vm.runInContext(read('activity.js'),context);vm.runInContext(read('app.js'),context);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await tick();
 const input=el('#files');input.files=[{name:'real.jpg',size:1024}];
 const upload=input.onchange({target:input});await started;
 assert.equal(el('#activity').open,true);assert.match(el('#activityTitle').textContent,/正在上传/);assert.equal(el('#upload').disabled,true);
 rows=[{id:1,name:'real.jpg',batch:'test',state:'running',review:'pending',demo:0}];resolveImport();await upload;
 assert.match(el('#activityTitle').textContent,/正在分析/);assert.equal(el('#activityBackground').hidden,false);assert.equal(el('#upload').disabled,false);
 el('#activityBackground').onclick();assert.equal(el('#activity').open,false);assert.equal(el('#activityBar').hidden,false);
 rows=[{...rows[0],state:'failed',error:'服务暂不可用'}];await vm.runInContext('refresh()',context);
 assert.match(el('#activityBar').textContent,/处理完成/);
 el('#activityBar').onclick();assert.match(el('#activityMessage').textContent,/失败 1 张/);assert.equal(el('#activityDone').hidden,false);assert.equal(el('#activitySpinner').hidden,true);
 el('#activityDone').onclick();assert.equal(el('#activity').open,false);assert.equal(el('#activityBar').hidden,true);
 console.log('App flow test passed: delayed upload -> analysis -> background -> failure summary -> dismiss.');
})().catch(e=>{console.error(e);process.exitCode=1;});
