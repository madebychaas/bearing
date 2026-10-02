import test from 'node:test';
import assert from 'node:assert/strict';
import {topStoryItems,topStoryEvent,topStoryArtURL} from '../dist/producer.js';

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
