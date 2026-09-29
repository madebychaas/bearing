import test from 'node:test';
import assert from 'node:assert/strict';
import {rankedCandidates,candidatePage,safeSourceURL,freshnessLabel,relativeTime,readableReportingText,localSignalSources} from '../dist/producer.js';

const event=(id,extra={})=>({id,title:id,eligible:true,decision:{action:'none'},signals:{},...extra});
const snapshot={events:[event('urgent'),event('explain'),event('held',{eligible:false,whyNow:{status:'stale'}}),event('dismissed-update',{decision:{action:'dismiss'},signals:{update:true}})],rankings:{brief:['urgent','explain','held','dismissed-update'],focus:['explain','urgent','held','dismissed-update']}};

test('Brief and Focus retain their own ranking; held items stay accessible outside top candidates',()=>{
 assert.deepEqual(rankedCandidates(snapshot,'brief').map(item=>item.id),['urgent','explain']);
 assert.deepEqual(rankedCandidates(snapshot,'focus').map(item=>item.id),['explain','urgent']);
 assert.deepEqual(rankedCandidates(snapshot,'brief','alternatives').map(item=>item.id),['held']);
});
test('a changed dismissed story resurfaces for inspection without resetting the human decision',()=>{
 const updates=rankedCandidates(snapshot,'brief','updates');
 assert.equal(updates[0].id,'dismissed-update');assert.equal(updates[0].decision.action,'dismiss');
 assert.deepEqual(rankedCandidates(snapshot,'brief','dismissed').map(item=>item.id),['dismissed-update']);
});
test('eight-item pages remain navigable when the pool shrinks during a refresh',()=>{
 const many={events:Array.from({length:19},(_,i)=>event(String(i))),rankings:{brief:Array.from({length:19},(_,i)=>String(i))}};
 assert.equal(candidatePage(many,'brief','all').items.length,8);
 assert.deepEqual(candidatePage(many,'brief','all',1).items.map(item=>item.id),['8','9','10','11','12','13','14','15']);
 const clamped=candidatePage(snapshot,'brief','all',8);assert.equal(clamped.page,0);assert.equal(clamped.total,2);
});
test('source links allow only ordinary external web URLs without embedded credentials',()=>{
 assert.equal(safeSourceURL('https://www.nist.gov/news'), 'https://www.nist.gov/news');
 for(const unsafe of ['javascript:alert(1)','data:text/html,<script>','file:///secret','https://password:secret@example.com/','/relative','not a URL'])assert.equal(safeSourceURL(unsafe),null);
});
test('refreshing a view cannot relabel stale, future or unknown evidence as fresh',()=>{
 assert.equal(freshnessLabel({whyNow:{status:'stale'}}),'Older reporting');
 assert.equal(freshnessLabel({whyNow:{status:'future'}}),'Future-dated');
 assert.equal(relativeTime('2026-09-28T12:00:00Z','2026-09-29T12:00:00Z'),'1d ago');
 assert.equal(relativeTime('2026-09-30T12:00:00Z','2026-09-29T12:00:00Z'),'Future-dated');
 assert.equal(relativeTime(null,'2026-09-29T12:00:00Z'),'Time unverified');
 assert.ok(!readableReportingText('Published at 2026-09-29T12:00:00Z.').includes('T12:00'));
});
test('local pattern references resolve across stories without adding unrelated or duplicate sources',()=>{
 const reporting={events:[{id:'a',evidence:[{id:'report-a',publisher:'Local One',market:'Houston',title:'Insurance reporting',url:'https://example.com/a'},{id:'wire',publisher:'Wire',market:'Dallas',title:'Syndicated copy'}]},{id:'b',evidence:[{id:'report-b',publisher:'Local Two',market:'Tampa',title:'Renewal reporting',url:'https://example.com/b'}]}]};
 const basis=localSignalSources(reporting,{reportIds:['report-b','report-a','report-b','missing']});
 assert.deepEqual(basis.reports.map(report=>[report.id,report.market,report.eventId]),[['report-b','Tampa','b'],['report-a','Houston','a']]);
 assert.deepEqual(basis.missingIds,['missing']);
 assert.equal(basis.reports[0].url,'https://example.com/b');
 assert.deepEqual(localSignalSources(reporting,null),{reports:[],missingIds:[]});
});
