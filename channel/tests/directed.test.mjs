import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {directedSceneAt,revealProgress,courtesyAt} from '../dist/directed.js';
const edition=JSON.parse(fs.readFileSync(new URL('../dist/programmes.json',import.meta.url),'utf8'));
const story=edition.stories.find(s=>s.programme.visualTreatment==='directed');
test('courtesy and campus photograph are scoped to their spoken scene in both voices',()=>{
 assert.ok(story);
 for(const track of Object.values(story.voices)){
  const place=track.visualCues.find(c=>story.programme.beats[c.beat].kind==='place');
  assert.equal(courtesyAt(story,track,place.start-.001,'story'),null);
  assert.equal(courtesyAt(story,track,place.start,'story').author,'RJN');
  assert.equal(courtesyAt(story,track,place.end,'closing'),null);
  assert.equal(courtesyAt(story,track,place.start-.001,'story'),null);
  assert.equal(directedSceneAt(track,track.chapters[1].start),null);
 }
});
test('reveals respect word timing, pause, backwards seek and reduced motion',()=>{
 assert.equal(revealProgress(12,11.99),0);
 assert.ok(Math.abs(revealProgress(12,12.325)-.5)<1e-12);
 assert.equal(revealProgress(12,13),1);
 assert.equal(revealProgress(12,11),0);
 assert.equal(revealProgress(12,12,1,true),1);
 assert.equal(revealProgress(12,11.99,1,true),0);
});
test('every delivered scene reveal falls within its narration-scoped scene',()=>{
 for(const track of Object.values(story.voices))for(const scene of track.visualCues){
  for(const reveal of scene.reveals){assert.ok(reveal.start>=scene.start);assert.ok(reveal.start<scene.end);}
  assert.ok(track.wordTimings.length>=60);assert.equal(track.provider,'kokoro-local-cpu');
 }
});
