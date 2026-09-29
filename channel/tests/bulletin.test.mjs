import test from 'node:test';
import assert from 'node:assert/strict';
import {orderedClips,validClip} from '../dist/bulletin.js';
const now=Date.parse('2026-09-29T01:00:00Z');
const item=(id,topic,minutes=10)=>({id,topic,title:`Story ${id}`,publishedTime:new Date(now-minutes*60000).toISOString(),source:{url:`https://example.com/${id}`}});
test('video queue interleaves fresh interests and excludes stale clips',()=>{
 const stories=[item('w1','world',1),item('w2','world',2),item('s1','sport',3),item('c1','culture',4),item('old','world',1500)];
 assert.deepEqual(orderedClips(stories,{now}).map(s=>s.id),['w1','s1','c1','w2']);
 assert.deepEqual(orderedClips(stories,{now,topics:['sport'],hours:1}).map(s=>s.id),['s1']);
});
test('partial media and unsafe asset paths cannot enter the video player',()=>{
 const clip={...item('a','world'),status:'ready',format:'headline-video',image:'assets/latest/a.png',voices:{warm:{video:'assets/latest/a-warm.mp4',duration:12,captions:[]},measured:{video:'assets/latest/a-measured.mp4',duration:13,captions:[]}}};
 assert.equal(validClip(clip),true);
 assert.equal(validClip({...clip,voices:{warm:clip.voices.warm}}),false);
 assert.equal(validClip({...clip,image:'assets/../../private.png'}),false);
});
