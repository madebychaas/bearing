import test from 'node:test';
import assert from 'node:assert/strict';
import {rankedCandidates,candidatePage,candidateFilters,assignmentPegSource,discoveryLag,sourceClockLabel,assignmentReportClock} from '../dist/producer.js';

const event=(id,scope,lane,priority=10,extra={})=>({id,title:id,eligible:true,assignment:{scope,lane,priority},...extra});
const snapshot={assignment:{},events:[
 event('today','national','today',80),event('world','world-impact','today',90),
 event('developing','national','developing',70),event('watch','national','watch',40),
 event('local','local','today',99),event('unknown','unestablished','today',99),
 event('held','national','held',20,{eligible:false}),
 event('dismissed','national','today',99,{decision:{action:'dismiss'}}),
 event('local-saved','local','held',5,{decision:{action:'shortlist'}})
],rankings:{brief:['today','developing','local','unknown','world','held','watch','dismissed','local-saved'],focus:['world','developing','today','local','unknown','held','watch','dismissed','local-saved']}};

test('live national lanes exclude local and unestablished signals even with high priority',()=>{
 assert.deepEqual(rankedCandidates(snapshot,'brief','today').map(e=>e.id),['world','today']);
 assert.deepEqual(rankedCandidates(snapshot,'brief','developing').map(e=>e.id),['developing']);
 assert.deepEqual(rankedCandidates(snapshot,'brief','watch').map(e=>e.id),['watch']);
 assert.deepEqual(rankedCandidates(snapshot,'brief','all').map(e=>e.id),['world','today','developing','watch','held']);
});
test('held and out-of-scope records remain inspectable without losing decisions',()=>{
 assert.deepEqual(rankedCandidates(snapshot,'brief','alternatives').map(e=>e.id),['local','unknown','held','local-saved']);
 assert.deepEqual(rankedCandidates(snapshot,'brief','shortlist').map(e=>e.id),['local-saved']);
 assert.deepEqual(rankedCandidates(snapshot,'brief','dismissed').map(e=>e.id),['dismissed']);
 assert.equal(snapshot.events.find(e=>e.id==='local-saved').decision.action,'shortlist');
});
test('equal assignment priorities preserve product rank and empty lanes have no fallback story',()=>{
 const equal={...snapshot,events:snapshot.events.map(e=>({...e,assignment:{...e.assignment,priority:1}}))};
 assert.deepEqual(rankedCandidates(equal,'brief','today').map(e=>e.id),['today','world']);
 assert.deepEqual(rankedCandidates(equal,'focus','today').map(e=>e.id),['world','today']);
 const empty=candidatePage({...snapshot,events:[]},'brief','today');
 assert.equal(empty.total,0);assert.deepEqual(empty.items,[]);
});
test('legacy and synthetic cycles retain original filters without national classifications',()=>{
 assert.equal(candidateFilters(snapshot)[0][0],'today');
 assert.equal(candidateFilters({mode:'demo'})[0][0],'all');
 assert.ok(candidateFilters({mode:'demo'}).some(([id])=>id==='local'));
 const legacy={events:[{id:'local',localSignal:{},eligible:true}],rankings:{brief:['local']}};
 assert.equal(rankedCandidates(legacy,'brief','local').length,1);
});
test('a today peg resolves only its exact carried report, never an unrelated fallback',()=>{
 const story={assignment:{todayPeg:{sourceId:'report-2'}},evidence:[{id:'report-1',publisher:'One'},{id:'report-2',publisher:'Two'}]};
 assert.equal(assignmentPegSource(story).publisher,'Two');
 assert.equal(assignmentPegSource({...story,evidence:[story.evidence[0]]}),null);
 assert.equal(assignmentPegSource({}),null);
});
test('discovery-lag copy distinguishes zero, missing and invalid observations',()=>{
 assert.equal(discoveryLag(0),'Under 1 min');assert.equal(discoveryLag(12.1),'12 min');
 assert.equal(discoveryLag(150),'2.5 hr');
 for(const value of [null,undefined,-1,NaN,'2'])assert.equal(discoveryLag(value),'Not measured');
});
test('public-inspection filings and update clocks are not labeled as publication',()=>{
 assert.equal(sourceClockLabel({sourceTimeKind:'filed'}),'Filed');
 assert.equal(sourceClockLabel({sourceTimeKind:'updated'}),'Updated');
 assert.equal(sourceClockLabel({sourceTimeKind:'published'}),'Published');
});
test('assignment time and label belong to the exact peg report, not the newest report or observed change',()=>{
 const story={assignment:{todayPeg:{sourceId:'filing',kind:'changed-reporting',at:'2026-10-02T14:00:00Z'}},whyNow:{at:'2026-10-02T13:00:00Z'},evidence:[
  {id:'filing',sourceTimeKind:'filed',publishedAt:'2026-10-02T11:00:00Z'},
  {id:'new-report',sourceTimeKind:'published',publishedAt:'2026-10-02T13:00:00Z'}
 ]};
 assert.deepEqual(assignmentReportClock(story),{label:'Filed',at:'2026-10-02T11:00:00Z'});
 assert.deepEqual(assignmentReportClock({...story,evidence:[story.evidence[1]]}),{label:'Source time',at:null});
 assert.deepEqual(assignmentReportClock({...story,evidence:[{id:'filing',sourceTimeKind:'updated'}]}),{label:'Updated',at:null});
});
