import test from 'node:test';
import assert from 'node:assert/strict';
import {selectRecent,changedReports,sourceHealth,relativeTime} from '../dist/live-news.js';
const now=Date.parse('2026-09-28T23:00:00Z');
const item=(id,publishedTime,topic='world')=>({id,publishedTime,topic,title:`Report ${id}`,version:id,source:{url:`https://example.com/${id}`}});
test('recency excludes old, future, and date-only reports regardless of retrieval time',()=>{
 const reports=[item('old','2026-09-26T22:00:00Z'),item('future','2026-09-29T00:00:00Z'),item('day','2026-09-28'),item('recent','2026-09-28T22:40:00Z')].map(s=>({...s,retrievedAt:'2026-09-28T23:00:00Z'}));
 assert.deepEqual(selectRecent(reports,{hours:24,now}).map(s=>s.id),['recent']);
});
test('recent reports sort by precise publication time, filter interests, and deduplicate URLs',()=>{
 const a=item('a','2026-09-28T22:00:00Z','culture'),b=item('b','2026-09-28T22:50:00Z'),c=item('c','2026-09-28T22:30:00Z');
 assert.deepEqual(selectRecent([a,b,c,b],{now}).map(s=>s.id),['b','c','a']);
 assert.deepEqual(selectRecent([a,b,c],{topics:['culture'],now}).map(s=>s.id),['a']);
});
test('same-URL revisions count as updates; repeated fetches do not',()=>{
 const a=item('a','2026-09-28T22:00:00Z');
 assert.equal(changedReports([a],[{...a,retrievedAt:'later'}]).length,0);
 assert.equal(changedReports([a],[{...a,title:'Revised headline',version:'v2'}]).length,1);
});
test('connection state distinguishes a fresh worker, partial outage, and stale snapshot',()=>{
 assert.equal(sourceHealth({checkedAt:'2026-09-28T22:59:00Z',healthy:20,total:20},now).state,'healthy');
 assert.equal(sourceHealth({checkedAt:'2026-09-28T22:59:00Z',healthy:19,total:20},now).state,'partial');
 assert.equal(sourceHealth({checkedAt:'2026-09-28T22:59:00Z',healthy:0,total:20},now).state,'offline');
 assert.equal(sourceHealth({checkedAt:'2026-09-28T22:50:00Z',healthy:20,total:20},now).state,'delayed');
});
test('relative time uses the report timestamp',()=>{
 assert.equal(relativeTime('2026-09-28T22:35:00Z',now),'25 min ago');
 assert.equal(relativeTime('2026-09-28T21:00:00Z',now),'2 hours ago');
});
