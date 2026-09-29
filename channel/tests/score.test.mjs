import test from 'node:test';
import assert from 'node:assert/strict';
import {scoreGainAt,smoothGain,soundCueAt} from '../dist/studio.js';

test('authored score enters under the lead, ducks speech and resolves before the boundary',()=>{
 const captions=[{start:.45,end:4},{start:5,end:23}];
 assert.equal(scoreGainAt(captions,0,24,.12),0);
 assert.ok(scoreGainAt(captions,.1,24,.12)>0);
 assert.ok(scoreGainAt(captions,1,24,.12)<scoreGainAt(captions,4.5,24,.12));
 assert.ok(scoreGainAt(captions,23.9,24,.12)<scoreGainAt(captions,23.5,24,.12));
 assert.equal(scoreGainAt(captions,24,24,.12),0);
 assert.equal(scoreGainAt(captions,1,24,0),0);
});

test('ducking speed is consistent across display refresh rates and does not overshoot',()=>{
 const fade=(hz)=>{let gain=.12;for(let i=0;i<hz;i++)gain=smoothGain(gain,.03,1/hz);return gain;};
 assert.ok(Math.abs(fade(30)-fade(144))<1e-10);
 assert.ok(fade(60)>=.03&&fade(60)<.031);
 assert.equal(smoothGain(.04,.08,0),.04);
});

test('early pause and resume does not restart the signature, while a new playback can',()=>{
 const first={kind:'ident',lastKind:'opening',time:0,lastTime:0,justStarted:true,treatment:'editorial-score'};
 assert.equal(soundCueAt(first),'ident');
 assert.equal(soundCueAt({...first,kind:'ident',lastKind:'ident',time:.12,lastTime:.12,introPlayed:true}),null);
 assert.equal(soundCueAt({...first,introPlayed:false}),'ident');
 assert.equal(soundCueAt({...first,seeking:true}),null);
});

test('opening transition lets the signature ring and seeking cannot fire a closing cue',()=>{
 const crossing={kind:'opening',lastKind:'ident',time:.35,lastTime:.34,treatment:'editorial-score',introPlayed:true};
 assert.equal(soundCueAt(crossing),null);
 const ending={...crossing,kind:'closing',lastKind:'closing',time:22,lastTime:21.99,resolveAt:22};
 assert.equal(soundCueAt(ending),'resolve');
 assert.equal(soundCueAt({...ending,seeking:true}),null);
 assert.equal(soundCueAt({...ending,lastTime:5}),null);
 assert.equal(soundCueAt({...ending,kind:'outro',lastKind:'closing',time:23,lastTime:22.99}),null);
});
