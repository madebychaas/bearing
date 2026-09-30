import test from 'node:test';
import assert from 'node:assert/strict';
import {handoffActions,handoffPreviewURL,handoffScriptWords,handoffDraft} from '../dist/producer.js';

const ready={state:'draft',draft:{},prepared:{packet:{}},revision:2};
test('review approval requires a named review of saved copy and a prepared plan',()=>{
 assert.equal(handoffActions(ready,{actor:'Editor',reviewed:true}).approve,true);
 for(const options of [{reviewed:true},{actor:'Editor'},{actor:'Editor',reviewed:true,dirty:true},{actor:'Editor',reviewed:true,busy:true}])assert.equal(handoffActions(ready,options).approve,false);
 assert.equal(handoffActions({...ready,prepared:null},{actor:'Editor',reviewed:true}).approve,false);
 assert.equal(handoffActions({...ready,state:'approved',approval:{}}).produce,true);
 assert.equal(handoffActions(ready).produce,false);
});
test('changed reporting and in-progress production block stale completion',()=>{
 const changed={...ready,state:'needs-reassessment',approval:{},reassessment:{required:true}};
 const result=handoffActions(changed,{actor:'Editor',reviewed:true});
 assert.equal(result.approve,false);assert.equal(result.produce,false);assert.equal(result.reassess,true);
 assert.equal(result.review,true,'a producer may still hold or reject changed work');
 for(const state of [{state:'producing'},{production:{state:'running'}}]){
  const active=handoffActions({...ready,...state},{actor:'Editor',reviewed:true});
  assert.equal(active.save,false);assert.equal(active.approve,false);assert.equal(active.produce,false);
  assert.equal(active.review,true,'hold and reject remain available to revoke running work');
 }
});
test('finished preview links accept only local film artifacts',()=>{
 assert.equal(handoffPreviewURL('assets/films/version/warm.mp4'),'/assets/films/version/warm.mp4');
 for(const value of ['https://evil.test/assets/films/warm.mp4','//evil.test/assets/films/warm.mp4','javascript:alert(1)','/assets/films/../../secrets.mp4','/production/secret.mp4','assets\\films\\a.mp4','assets/films/a.mp4?redirect=1'])assert.equal(handoffPreviewURL(value),null);
});
test('script edits preserve every citation and existing visual evidence until visual intent changes',()=>{
 const refs=[{id:'a',quote:'A sufficiently exact source excerpt.'},{id:'b',quote:'Another exact supporting source.'}];
 const visuals=[{kind:'chart',purpose:'Compare supported figures',description:'Reveal figures when spoken.',evidenceIds:['a','b']}];
 const fields={title:' Revised title ',opening:[{text:'A new public service is open.',evidence:refs}],body:[{text:'Officials explain how it works.',evidence:[refs[0]]}],closing:[{text:'Here is the next step.',evidence:[refs[1]]}],visualIntent:visuals[0].description,pronunciations:'name — pronunciation',issues:''};
 const draft=handoffDraft({draft:{visuals}},fields);
 assert.deepEqual(draft.opening[0].evidence,refs);assert.deepEqual(draft.visuals,visuals);assert.notEqual(draft.visuals,visuals);assert.equal(draft.title,'Revised title');assert.equal(handoffScriptWords(draft),16);
 const revised=handoffDraft({draft:{visuals}},{...fields,visualIntent:'An original explanatory flow.'});
 assert.deepEqual(revised.visuals[0].evidenceIds,['a','b']);assert.equal(revised.visuals[0].description,'An original explanatory flow.');
});
