/* Batch activity state shared by the UI and dependency-free Node tests. */
class WorkProgress {
  constructor(){this.ids=new Set();this.uploading=false;this.total=0;this.processed=0;this.added=0;this.duplicates=0;this.errors=[];this.current='';this.started=0;}
  begin(total){this.ids.clear();this.uploading=true;this.total=total;this.processed=0;this.added=0;this.duplicates=0;this.errors=[];this.started=Date.now();}
  accept(id,duplicate=false){this.processed++;if(duplicate)this.duplicates++;else{this.added++;this.ids.add(id);}}
  reject(message){this.processed++;this.errors.push(message);}
  finish(){this.uploading=false;}
  analyze(id){if(!this.ids.size)this.started=Date.now();this.ids.add(id);}
  snapshot(items){const byId=new Map(items.map(x=>[x.id,x]));let done=0,failed=0,pending=0;for(const id of this.ids){const x=byId.get(id);if(x?.state==='done')done++;else if(x?.state==='failed')failed++;else pending++;}return{done,failed,pending,total:this.ids.size,complete:!this.uploading&&pending===0};}
}
if(typeof module!=='undefined')module.exports=WorkProgress;
else globalThis.WorkProgress=WorkProgress;
