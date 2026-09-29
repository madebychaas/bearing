import test from 'node:test';
import assert from 'node:assert/strict';
import {startCamera,cameraError} from '../dist/camera-player.js';

function fixture(t){
 const previous={document:globalThis.document,location:globalThis.location};
 const frame={remove(){this.removed=true;}};let events,player;
 globalThis.document={createElement:()=>frame};globalThis.location={origin:'http://127.0.0.1:8796'};
 t.after(()=>{for(const [key,value] of Object.entries(previous)){if(value===undefined)delete globalThis[key];else globalThis[key]=value;}});
 const states=[];const screen={append(node){assert.equal(node,frame);}};
 const YT={Player:class {constructor(_frame,options){events=options.events;player=this;}mute(){this.muted=true;}playVideo(){this.requested=true;}destroy(){this.destroyed=true;}}};
 return {frame,states,screen,YT,get events(){return events;},get player(){return player;},onStatus:(state,text)=>states.push({state,text})};
}

test('camera starts muted and reports playing only after the provider confirms it',async t=>{
 const f=fixture(t);const close=startCamera({...f,videoId:'HggWKlZv9yk',loadAPI:()=>Promise.resolve(f.YT)});t.after(close);
 await Promise.resolve();assert.equal(f.states.at(-1).state,'loading');
 const url=new URL(f.frame.src);assert.equal(url.origin,'https://www.youtube.com');assert.equal(url.searchParams.get('origin'),location.origin);
 f.events.onReady({target:f.player});assert.ok(f.player.muted&&f.player.requested);assert.equal(f.states.at(-1).state,'loading');
 f.events.onStateChange({data:1});assert.equal(f.states.at(-1).state,'playing');
 close();assert.ok(f.player.destroyed&&f.frame.removed);
});
test('closing while the API is loading never creates a late player',async t=>{
 const f=fixture(t);let ready;const close=startCamera({...f,videoId:'HggWKlZv9yk',loadAPI:()=>new Promise(resolve=>ready=resolve)});
 close();ready(f.YT);await Promise.resolve();assert.equal(f.player,undefined);
});
test('autoplay blocks and embed errors are actionable, never reported as playing',async t=>{
 const f=fixture(t);const close=startCamera({...f,videoId:'HggWKlZv9yk',loadAPI:()=>Promise.resolve(f.YT)});t.after(close);await Promise.resolve();
 f.events.onAutoplayBlocked();assert.equal(f.states.at(-1).state,'blocked');
 f.events.onError({data:153});assert.match(f.states.at(-1).text,/identity/);assert.equal(f.states.at(-1).state,'unavailable');
 assert.match(cameraError(100),/no longer available/);assert.match(cameraError(150),/does not allow/);
});
test('silent frame failures time out with recovery instructions',async t=>{
 const f=fixture(t);const close=startCamera({...f,videoId:'HggWKlZv9yk',loadAPI:()=>Promise.resolve(f.YT),timeoutMs:5});t.after(close);
 await new Promise(resolve=>setTimeout(resolve,15));assert.equal(f.states.at(-1).state,'unavailable');assert.match(f.states.at(-1).text,/Try again/);
 close();f.events.onStateChange({data:1});assert.equal(f.states.at(-1).state,'unavailable');
});
