import test from 'node:test';
import assert from 'node:assert/strict';
import {balancedRotation} from '../dist/rotation.js';

const stories = ['space','space','space','nature','nature','nature','nature','culture','world','business','technology'].map((topic,i)=>({id:String(i),topic}));
test('a broad selection gets no more than two stories from any one topic per lap',()=>{
 const lap=balancedRotation(stories);
 assert.equal(lap.length,8);
 for(const topic of new Set(lap.map(s=>s.topic))) assert.ok(lap.filter(s=>s.topic===topic).length<=2);
 assert.equal(new Set(lap.map(s=>s.id)).size,lap.length);
 assert.equal(new Set(lap.slice(0,6).map(s=>s.topic)).size,6);
});
test('stories outside the first lap remain reachable on subsequent laps',()=>{
 const reached=new Set(Array.from({length:4},(_,i)=>balancedRotation(stories,i)).flat().map(s=>s.id));
 assert.deepEqual(reached,new Set(stories.map(s=>s.id)));
});
test('one or two selected topics keep every available story',()=>{
 for(const topics of [['nature'],['nature','space']]){
  const selected=stories.filter(s=>topics.includes(s.topic));
  assert.equal(balancedRotation(selected).length,selected.length);
 }
 assert.deepEqual(balancedRotation([]),[]);
});
