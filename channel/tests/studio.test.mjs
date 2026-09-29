import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {phaseAt,visualBeatAt} from '../dist/studio.js';
import {validClip} from '../dist/bulletin.js';
const edition=JSON.parse(fs.readFileSync(new URL('../dist/programmes.json',import.meta.url),'utf8'));
test('all studio stories contain complete, ordered, seekable chapters in both voices',()=>{
 assert.ok(edition.stories.length>=11);
 for(const story of edition.stories){
  assert.equal(validClip(story),true);
  assert.ok(story.programme.why&&story.programme.summary&&story.programme.lookAhead);
  for(const voice of Object.values(story.voices)){
   assert.deepEqual(voice.chapters.map(c=>c.kind),['ident','opening','story','closing','outro']);
   for(const [i,c] of voice.chapters.entries()){
    assert.equal(phaseAt(voice.chapters,c.start).kind,c.kind);
    assert.ok(c.end>c.start);if(i)assert.equal(c.start,voice.chapters[i-1].end);
   }
   assert.equal(voice.chapters.at(-1).end,voice.duration);
   assert.ok(voice.captions.every(c=>c.end>c.start&&c.start>=0&&c.end<=voice.duration));
  }
 }
});
test('seeking backwards selects the right chapter, including exact boundaries',()=>{
 const chapters=edition.stories[0].voices.warm.chapters;
 assert.equal(phaseAt(chapters,chapters[3].start).kind,'closing');
 assert.equal(phaseAt(chapters,chapters[1].start).kind,'opening');
 assert.equal(phaseAt(chapters,0).kind,'ident');
 assert.equal(phaseAt(chapters,10000).kind,'outro');
 assert.equal(phaseAt([],0),null);
});

test('narration cues change graphics at spoken boundaries, including backwards seeks',()=>{
 const story={programme:{beats:[{text:'Funding'},{text:'Training'},{text:'Outcomes'}]}};
 const track={chapters:[{kind:'story',start:10,end:60}],visualCues:[{start:10,end:19,beat:0},{start:19,end:48,beat:1},{start:48,end:60,beat:2}]};
 assert.equal(visualBeatAt(story,track,18.99).value.text,'Funding');
 assert.equal(visualBeatAt(story,track,19).value.text,'Training');
 assert.equal(visualBeatAt(story,track,49).value.text,'Outcomes');
 assert.equal(visualBeatAt(story,track,20).value.text,'Training');
});
