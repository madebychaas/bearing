import test from 'node:test';
import assert from 'node:assert/strict';
import {createFilmChrome} from '../dist/film-chrome.js';

const story={programme:{visualTreatment:'finished-film',pictureTreatment:'full-frame-v2'}};
function setup(){
 const handlers={},pending=new Map();let counter=0;
 const host={dataset:{},ownerDocument:{activeElement:null},contains:node=>node.inside,addEventListener:(name,callback)=>handlers[name]=callback};
 const controls=createFilmChrome({host,schedule:fn=>{pending.set(++counter,fn);return counter;},cancel:id=>pending.delete(id)});
 return {host,controls,event:name=>handlers[name](),idle:()=>{const callbacks=[...pending.values()];pending.clear();for(const callback of callbacks)callback();},pending};
}
test('full-frame controls clear the picture during continuous playback and return on interaction',()=>{
 const page=setup();page.controls.update({story,started:true,playing:true});
 assert.equal(page.host.dataset.pictureTreatment,'full-frame-v2');assert.equal(page.host.dataset.controlsVisible,'true');
 page.idle();assert.equal(page.host.dataset.controlsVisible,'false');
 page.event('pointermove');assert.equal(page.host.dataset.controlsVisible,'true');
 page.idle();assert.equal(page.host.dataset.controlsVisible,'false');
 page.controls.update({story,started:true,playing:false});page.idle();assert.equal(page.host.dataset.controlsVisible,'true');
});
test('chapter and transport keyboard focus keeps controls visible until focus leaves',()=>{
 const page=setup();page.controls.update({story,started:true,playing:true});
 page.host.ownerDocument.activeElement={inside:true,matches:selector=>selector===':focus-visible'};
 page.event('focusin');page.idle();assert.equal(page.host.dataset.controlsVisible,'true');
 page.host.ownerDocument.activeElement=null;page.event('focusout');page.idle();assert.equal(page.host.dataset.controlsVisible,'false');
});
test('selecting another treatment cancels full-frame hiding without altering accepted films',()=>{
 const page=setup();page.controls.update({story,started:true,playing:true});assert.equal(page.pending.size,1);
 page.controls.update({story:{programme:{visualTreatment:'finished-film'}},started:true,playing:true});
 assert.equal(page.host.dataset.pictureTreatment,'');assert.equal(page.pending.size,0);
 page.event('pointermove');page.idle();assert.equal(page.host.dataset.controlsVisible,'true');
 page.controls.update({story,started:false,playing:false});page.idle();assert.equal(page.host.dataset.controlsVisible,'true');
});
