import test from 'node:test';
import assert from 'node:assert/strict';
import {catalogStories,toggleNewscastStory,selectionChanges,canMakeNewscast,newscastRequest,readyNewscast,personalQueue,nextPersonalStory,playerNewscastPreferences,jobIsActive,stageLabel} from '../dist/newscast-state.js';

const now=Date.parse('2026-10-01T20:00:00Z');
const report=(id='a',revision='one',publishedAt='2026-10-01T18:00:00Z')=>({id,revision,publishedAt,title:`Story ${id}`,publisher:'NPR',sourceUrl:`https://npr.org/${id}`,topic:'business'});
const film=id=>({id,title:`Story ${id}`,status:'ready',image:`assets/films/${id}/poster.png`,video:`assets/films/${id}/warm.mp4`,source:{name:'NPR',url:`https://npr.org/${id}`},visual:{scope:'story',storyId:id},programme:{visualTreatment:'finished-film'},expiresAt:'2026-10-02T20:00:00Z',voices:Object.fromEntries(['warm','measured'].map(voice=>[voice,{audio:`assets/films/${id}/${voice}.mp3`,video:`assets/films/${id}/${voice}.mp4`,duration:40,captions:[]}]))});
const readyJob=()=>({id:'newscast-proof',status:'ready',total:2,stories:[report('a'),report('b')],preferences:{voice:'warm',pace:'natural',music:'quiet'},result:{stories:['a','b'].map(id=>({...film(id),production:{newscast:{jobId:'newscast-proof',eventId:id,sourceRevision:'one'},selection:{eventId:id,approval:'approved'}}})),teaser:'Understand two changes that affect your household.'}});

test('catalog preserves source identity and publication recency while rejecting malformed rows',()=>{
 const first=report('a'),later=report('b','one','2026-10-01T19:00:00Z');
 const rows=catalogStories([first,later,first,{...report('c'),sourceUrl:'javascript:alert(1)'},{...report('d'),publishedAt:'not a time'},{...report('e'),publishedAt:'2026-10-03T00:00:00Z'}],now);
 assert.deepEqual(rows.map(row=>row.id),['b','a']);assert.equal(rows[0],later);
});
test('a viewer can choose two or three distinct stories and remove one without reordering',()=>{
 let selected=[];for(const id of ['a','b','c'])selected=toggleNewscastStory(selected,report(id)).selected;
 const full=toggleNewscastStory(selected,report('d'));assert.equal(full.selected,selected);assert.match(full.message,/Remove a story/);
 selected=toggleNewscastStory(selected,report('b')).selected;assert.deepEqual(selected.map(story=>story.id),['a','c']);
 assert.equal(canMakeNewscast(selected,selected,{generationReady:true}),true);
 assert.equal(canMakeNewscast([selected[0]],selected,{generationReady:true}),false);
 assert.equal(canMakeNewscast([...selected,...selected],selected,{generationReady:true}),false);
});
test('source revisions remain bound to the selection and refresh never silently accepts a change',()=>{
 const selected=[report('a'),report('b')],changed=[report('a','two'),report('b')];
 assert.deepEqual(selectionChanges(selected,changed),['a']);assert.equal(selected[0].revision,'one');
 assert.equal(canMakeNewscast(selected,changed,{generationReady:true}),false);
 assert.deepEqual(selectionChanges(selected,[changed[0]]),['a','b']);
 const updated=toggleNewscastStory(toggleNewscastStory(selected,selected[0]).selected,changed[0]).selected;
 assert.deepEqual(selectionChanges(updated,changed),[]);
});
test('connection-needed submissions save real choices without claiming automatic readiness',()=>{
 const selected=[report('a'),report('b')];assert.equal(canMakeNewscast(selected,selected,{generationReady:false}),true);
 assert.equal(canMakeNewscast(selected,selected,{generationReady:true},true),false);
 const request=newscastRequest(selected,{voice:'measured',pace:'unhurried',music:'off'},'request-id');
 assert.deepEqual(request,{stories:[{id:'a',revision:'one'},{id:'b',revision:'one'}],preferences:{voice:'measured',pace:'unhurried',music:'off'},requestId:'request-id'});
 assert.throws(()=>newscastRequest([selected[0],selected[0]],{},'request-id'));
});
test('only a complete, current, finished set is offered for playback',()=>{
 const job=readyJob();assert.equal(readyNewscast(job,now).stories.length,2);
 for(const status of ['queued','working','failed','needs_attention','interrupted','cancelled'])assert.equal(readyNewscast({...job,status},now),null);
 assert.equal(readyNewscast({...job,total:3},now),null);
 for(const mutate of [value=>value.result.stories.pop(),value=>value.result.stories[1]=value.result.stories[0],value=>value.result.stories[0].programme.visualTreatment='directed',value=>delete value.result.stories[0].voices.measured.video,value=>value.result.stories[0].expiresAt='2026-09-30T00:00:00Z',value=>value.result.stories[0].expiresAt='not a date',value=>value.result.teaser='']){const bad=readyJob();mutate(bad);assert.equal(readyNewscast(bad,now),null);}
});
test('the ready snapshot is isolated and duration reflects voice and authored transition time',()=>{
 const job=readyJob();job.preferences.pace='unhurried';job.preferences.voice='measured';job.result.stories[0].voices.measured.duration=46;
 const ready=readyNewscast(job,now);assert.equal(ready.duration,86/.92+1.5);
 job.result.stories[0].title='Changed elsewhere';assert.equal(ready.stories[0].title,'Story a');
 ready.stories[0].voices.warm.duration=30;assert.equal(job.result.stories[0].voices.warm.duration,40);
 assert.deepEqual(ready.selection,[{id:'a',revision:'one'},{id:'b',revision:'one'}]);
});
test('finished results stay bound to this job and each original selection in its chosen order',()=>{
 for(const mutate of [job=>job.result.stories.reverse(),job=>job.result.stories[0].production.newscast.jobId='another-job',job=>job.result.stories[0].production.newscast.sourceRevision='another-revision',job=>job.result.stories[0].production.newscast.eventId='another-event',job=>delete job.result.stories[0].production.selection.approval,job=>delete job.stories]){const job=readyJob();mutate(job);assert.equal(readyNewscast(job,now),null);}
 const job=readyJob(),snapshot=readyNewscast(job,now);
 const replay={id:snapshot.id,status:'ready',total:2,stories:snapshot.selection,preferences:snapshot.preferences,result:snapshot};
 assert.ok(readyNewscast(replay,now));
 replay.stories[0].revision='changed';assert.equal(readyNewscast(replay,now),null);
});
test('the private queue follows only the chosen order and ends rather than looping or injecting news',()=>{
 const stories=[film('c'),film('a'),film('b')],failed=new Set(['a']);
 assert.deepEqual(personalQueue(stories,failed).map(story=>story.id),['c','b']);
 assert.equal(nextPersonalStory(stories,'c',failed).id,'b');assert.equal(nextPersonalStory(stories,'a',failed).id,'b');
 assert.equal(nextPersonalStory(stories,'b',failed),null);assert.equal(nextPersonalStory(stories,'c',new Set(['a','b'])),null);
 assert.deepEqual(stories.map(story=>story.id),['c','a','b']);
});
test('generation choices change the personal viewing session without mutating saved channel preferences',()=>{
 const original={topics:['business'],voice:'warm',pace:1.15,music:'piano',musicVolume:.25,captions:true,transitionSounds:true};
 const privatePrefs=playerNewscastPreferences(original,{voice:'measured',pace:'unhurried',music:'off'});
 assert.equal(privatePrefs.pace,.92);assert.equal(privatePrefs.voice,'measured');assert.equal(privatePrefs.music,'off');assert.equal(privatePrefs.transitionSounds,false);assert.equal(privatePrefs.captions,true);
 assert.equal(original.pace,1.15);assert.equal(original.music,'piano');assert.equal(original.transitionSounds,true);
});
test('status animation only represents genuine active work and stages have useful viewer language',()=>{
 assert.equal(jobIsActive({status:'working'}),true);assert.equal(jobIsActive({status:'queued'}),true);
 for(const status of ['needs_attention','failed','cancelled','interrupted','ready'])assert.equal(jobIsActive({status}),false);
 assert.equal(stageLabel('editing'),'Refining every line');assert.equal(stageLabel('unrecognized'),'Preparing your newscast');
});
