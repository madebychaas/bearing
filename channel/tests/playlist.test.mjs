import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {franchise,mergeEditions,selectPlaylist} from '../dist/playlist.js';
const edition=JSON.parse(fs.readFileSync(new URL('../dist/programmes.json',import.meta.url),'utf8'));
const short=JSON.parse(fs.readFileSync(new URL('../dist/latest-edition.json',import.meta.url),'utf8'));
test('a full story replaces its short version without duplicating the report',()=>{
 const full=edition.stories[0],brief={...short.stories[0],id:full.id,source:full.source};
 assert.deepEqual(mergeEditions([{stories:[brief]},{stories:[full]}]),[full]);
});
test('realtime playlist rejects stale, future and undated briefs, preserving dated features',()=>{
 const now=Date.parse('2026-09-28T23:00:00Z'),brief=short.stories[0];
 const candidates=['2026-09-26T00:00:00Z','2026-09-29T00:00:00Z','2026-09-28',null].map((publishedTime,i)=>({...brief,id:String(i),publishedTime}));
 assert.equal(selectPlaylist(candidates,{now}).length,0);
 const full={...edition.stories[0],expiresAt:null};
 assert.equal(selectPlaylist([full],{now}).length,1);
});
test('programme and topic choices constrain every playlist item',()=>{
 const full={...edition.stories.find(s=>s.topic==='nature'),expiresAt:null};
 const brief={...short.stories[0],publishedTime:new Date().toISOString()};
 const list=selectPlaylist([full,brief],{topics:['nature'],series:'field'});
 assert.deepEqual(list,[full]);assert.equal(franchise(full).name,'Field Notes');
 assert.equal(selectPlaylist([full],{failed:new Set([full.id])}).length,0);
});
test('chapter timing preserves legacy pauses and keeps directed narration within its budget',()=>{
 for(const story of edition.stories)for(const voice of Object.values(story.voices)){
  if(story.programme.visualTreatment==='directed'){
   assert.ok(voice.duration<=story.programme.maxDuration);
   assert.ok(voice.chapters[0].end>=1.5);
   assert.ok(voice.chapters.at(-1).end-voice.chapters.at(-1).start>=1.499);
   for(const chapter of voice.chapters.slice(1,-1)){
    const captions=voice.captions.filter(c=>c.start>=chapter.start&&c.end<=chapter.end);
    assert.ok(captions.length);assert.ok(captions[0].start>=chapter.start);
    assert.ok(captions.at(-1).end<=chapter.end);
   }
   continue;
  }
  assert.ok(voice.chapters[0].end>=4.5);
  assert.ok(voice.chapters.at(-1).end-voice.chapters.at(-1).start>=4.499);
  for(const chapter of voice.chapters.slice(1,-1)){
   const captions=voice.captions.filter(c=>c.start>=chapter.start&&c.end<=chapter.end);
   assert.ok(captions.length);
   assert.ok(captions[0].start-chapter.start>=1.799);
   assert.ok(chapter.end-captions.at(-1).end>=1.799);
  }
 }
});
