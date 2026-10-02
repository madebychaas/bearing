import test from 'node:test';
import assert from 'node:assert/strict';
import {topStoryItems,topStoryEvent,topStoryArtURL,heroIdentity,retainedHeroItems,currentStoryItems,prepareHeroItems} from '../dist/producer.js';

const snapshot={mode:'live',events:[{id:'one'},{id:'two'},{id:'three'},{id:'four'}],topStories:{items:[
 {eventId:'two',rank:1,headline:'A new report changes the picture'},
 {eventId:'one',rank:2,headline:'A major decision takes effect'},
 {eventId:'three',rank:3,headline:'A new national development'}
]}};

test('hero preserves the server editorial order instead of candidate or publication order',()=>{
 assert.deepEqual(topStoryItems(snapshot).map(item=>item.eventId),['two','one','three']);
 assert.equal(topStoryItems(snapshot)[0].headline,snapshot.topStories.items[0].headline);
});
test('missing, duplicate and malformed stories never create filler positions',()=>{
 const changed={...snapshot,topStories:{items:[snapshot.topStories.items[0],{eventId:'missing',headline:'Unavailable'},snapshot.topStories.items[0],{eventId:'one',headline:''},{eventId:'three',headline:'One other story'}]}};
 assert.deepEqual(topStoryItems(changed).map(item=>item.eventId),['two','three']);
 assert.deepEqual(topStoryItems({...snapshot,topStories:{items:[]}}),[]);
 assert.deepEqual(topStoryItems({...snapshot,topStories:undefined}),[]);
 assert.equal(topStoryItems({...snapshot,topStories:{items:[...snapshot.topStories.items,{eventId:'four',headline:'Fourth'}]}}).length,3);
});
test('a top story selects its exact underlying reporting even outside the current list filter',()=>{
 const filtered={...snapshot,rankings:{brief:['one']}};
 assert.equal(topStoryEvent(filtered,'two'),snapshot.events[1]);
 assert.equal(topStoryEvent(filtered,'missing'),null);
 assert.equal(topStoryEvent(null,'one'),null);
});
test('representative cycles never show live top stories',()=>{
 assert.deepEqual(topStoryItems({...snapshot,mode:'demo'}),[]);
});
test('hero art accepts only local original raster assets in its designated collection',()=>{
 for(const url of ['/assets/top-stories/jobs-report.webp','/assets/top-stories/2026-10-02/energy.png','/assets/top-stories/a.jpg'])assert.equal(topStoryArtURL(url),url);
 for(const url of ['https://publisher.example/news.jpg','//publisher.example/news.jpg','data:image/png;base64,x','/assets/films/art.webp','/assets/top-stories/a.svg','/assets/top-stories/../other/a.png','/assets/top-stories/%2e%2e/a.png','/assets/top-stories/a.png?new=1','/assets/top-stories/a.png#x','/assets/top-stories/a\\b.png',null,undefined])assert.equal(topStoryArtURL(url),null);
});

test('current stories continue the server edition and exclude displayed and reserved hero entries',()=>{
 const edition={...snapshot,events:[...snapshot.events,{id:'five'},{id:'six'}],topStories:{...snapshot.topStories,reservedEventIds:['two','one','three']},rankedStories:{items:[
  ...snapshot.topStories.items,{eventId:'four',rank:4,headline:'Fourth in significance'},{eventId:'five',rank:5,headline:'Fifth even if more recent'},{eventId:'six',rank:6,headline:'Sixth'}
 ]}};
 assert.deepEqual(currentStoryItems(edition,[{eventId:'one'}]).map(item=>[item.eventId,item.rank]),[['four',4],['five',5],['six',6]]);
 assert.equal(currentStoryItems({...edition,mode:'demo'}).length,0);
 assert.deepEqual(currentStoryItems({...edition,rankedStories:undefined}),[]);
 const fallback={...edition,topStories:{...edition.topStories,reservedEventIds:undefined}};
 assert.deepEqual(currentStoryItems(fallback,snapshot.topStories.items).map(item=>item.eventId),['four','five','six']);
});

test('ranked list does not paginate or invent items for an absent or malformed edition',()=>{
 const events=Array.from({length:20},(_,i)=>({id:`event-${i}`}));
 const edition={mode:'live',events,rankedStories:{items:events.map((event,i)=>({eventId:event.id,rank:i+4,headline:`Story ${i}`}))},topStories:{items:[]}};
 assert.equal(currentStoryItems(edition).length,20);
 assert.equal(currentStoryItems(edition).at(-1).rank,23);
 assert.equal(currentStoryItems({...edition,rankedStories:{items:[...edition.rankedStories.items,edition.rankedStories.items[0],{eventId:'missing',headline:'Missing report'}]}}).length,20);
});

const readyItem=(id,hash='original')=>({eventId:id,rank:1,headline:id,evidenceHash:hash,art:{url:`/assets/top-stories/${id}.png`,alt:id}});
test('retention requires continuing server authority over exact evidence and artwork',()=>{
 const prior=[readyItem('one'),readyItem('two')];
 const edition={...snapshot,topStories:{items:[readyItem('one'),readyItem('two','changed')]}};
 assert.deepEqual(retainedHeroItems(edition,prior),[prior[0]]);
 assert.deepEqual(retainedHeroItems({...edition,topStories:{items:[]}},prior),[]);
 assert.deepEqual(retainedHeroItems({...edition,topStories:{items:[{...prior[0],art:{url:'/assets/top-stories/new-art.png'}}]}},prior),[]);
 assert.deepEqual(retainedHeroItems({...edition,topStories:{items:[{...prior[0],evidenceHash:''}]}},[{...prior[0],evidenceHash:''}]),[]);
 assert.notEqual(heroIdentity(prior[0]),heroIdentity(readyItem('one','changed')));
});

test('hero preparation waits for every image decode before exposing any new tile',async()=>{
 const edition={...snapshot,topStories:{items:[readyItem('one'),readyItem('two')]}};
 let release,finished=false;const delayed=new Promise(resolve=>release=resolve);
 const prepared=prepareHeroItems(edition,async(url,item)=>item.eventId==='two'?await delayed:{decoded:true,url}).then(items=>{finished=true;return items;});
 await Promise.resolve();assert.equal(finished,false);
 release({decoded:true});const items=await prepared;
 assert.deepEqual(items.map(entry=>entry.item.eventId),['one','two']);
 assert.ok(items.every(entry=>entry.image.decoded));
});

test('failed or unsafe art cannot produce a half-ready hero tile',async()=>{
 const edition={...snapshot,topStories:{items:[readyItem('one'),readyItem('two'),{...readyItem('three'),art:{url:'https://example.com/remote.jpg'}}]}};
 const attempts=[];
 const items=await prepareHeroItems(edition,async(url,item)=>{attempts.push(item.eventId);if(item.eventId==='two')throw new Error('decode failed');return {decoded:true};});
 assert.deepEqual(items.map(entry=>entry.item.eventId),['one']);
 assert.deepEqual(attempts,['one','two']);
 assert.deepEqual(await prepareHeroItems({...edition,topStories:{items:[{...readyItem('one'),evidenceHash:''}]}},async()=>({decoded:true})),[]);
});
