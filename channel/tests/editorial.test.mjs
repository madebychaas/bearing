import test from 'node:test';
import assert from 'node:assert/strict';
import {curate} from '../dist/editorial.js';
test('US selection caps foreign publishers and excludes suppressed reports',()=>{
 const items=Array.from({length:40},(_,i)=>({id:i,editorial:{domestic:i>=10,score:100-i,publisher:i%2?'Axios':'NPR',suppressed:i===12,foreignLocal:i===1}}));
 const result=curate(items,{limit:20});
 assert.equal(result.length,20);assert.ok(result.filter(s=>!s.editorial.domestic).length<=2);
 assert.ok(!result.some(s=>[1,12].includes(s.id)));
});
test('US selection preserves upstream topic filtering',()=>{
 const items=[{id:1,topic:'nature',editorial:{domestic:true,score:35,publisher:'NASA'}}];
 assert.deepEqual(curate(items),items);
});
test('event grouping removes duplicate coverage but preserves a full package',()=>{
 const editorial={domestic:true,score:50,publisher:'NPR'};
 const items=[{id:'brief',format:'headline-video',editorial,coverage:{id:'event-one'}},{id:'full',format:'studio-programme',editorial:{...editorial,score:35},coverage:{id:'event-one'}},{id:'other',editorial,coverage:{id:'event-two'}}];
 assert.deepEqual(curate(items).map(s=>s.id).sort(),['full','other']);
});
