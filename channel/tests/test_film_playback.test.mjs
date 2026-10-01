import test from 'node:test';
import assert from 'node:assert/strict';
import {isFinishedFilm,pictureSource,editionFamily,reducedFilmFrame,syncFinishedPicture} from '../dist/film-playback.js';
import {mergeEditions,selectPlaylist,validStory} from '../dist/playlist.js';

const story={id:'film',status:'ready',title:'A reviewed current story',source:{url:'https://example.com/report'},image:'assets/films/poster.png',video:'assets/films/measured.mp4',format:'studio-programme',programme:{visualTreatment:'finished-film'},visual:{scope:'story',storyId:'film'},voices:{warm:{audio:'assets/films/warm.mp3',video:'assets/films/warm.mp4',duration:39,captions:[]},measured:{audio:'assets/films/measured.mp3',video:'assets/films/measured.mp4',duration:42,captions:[]}},topic:'business',expiresAt:'2026-10-01T00:00:00Z'};
const track={duration:42,chapters:[{kind:'ident',start:0},{kind:'opening',start:.35},{kind:'story',start:8},{kind:'closing',start:35}],openingCues:[{start:.45},{start:2.5}],visualCues:[{start:8,reveals:[{start:9},{start:12}]}],closingCues:[{start:35.1}]};
function film(){return {paused:true,loop:true,muted:false,currentTime:0,readyState:1,playbackRate:1,plays:0,pauses:0,play(){this.paused=false;this.plays++;return Promise.resolve();},pause(){this.paused=true;this.pauses++;}};}

test('each selected voice uses its own finished picture and keeps its edition separate',()=>{
 assert.equal(isFinishedFilm(story),true);assert.equal(pictureSource(story,'warm'),'assets/films/warm.mp4');assert.equal(pictureSource(story,'measured'),'assets/films/measured.mp4');
 assert.equal(editionFamily(story),'films.json');assert.equal(editionFamily({format:'headline-video'}),'latest-edition.json');assert.equal(editionFamily({format:'studio-programme'}),'programmes.json');
});
test('finished story supersedes the same sourced story while existing playlist expiry still applies',()=>{
 const prior={...story,id:'old',programme:{},visual:{scope:'story',storyId:'old'}};
 assert.deepEqual(mergeEditions([{stories:[story]},{stories:[prior]}]),[story]);
 assert.equal(selectPlaylist([story],{now:Date.parse('2026-09-30T20:00:00Z')}).length,1);
 assert.equal(selectPlaylist([story],{now:Date.parse('2026-10-01T01:00:00Z')}).length,0);
});
test('a finished film cannot enter the playlist without both safe voice-specific pictures',()=>{
 assert.equal(validStory(story),true);
 for(const invalid of [undefined,'https://example.com/movie.mp4','assets/../movie.mp4']){
  const broken=structuredClone(story);broken.voices.measured.video=invalid;assert.equal(validStory(broken),false);
 }
});
test('narration clock drives seek, playback rate and pause without playing embedded movie audio',()=>{
 const picture=film(),narration={currentTime:12.5,playbackRate:.85,paused:false};
 assert.equal(syncFinishedPicture({story,track,film:picture,narration,playing:true}),true);
 assert.equal(picture.currentTime,12.5);assert.equal(picture.playbackRate,.85);assert.equal(picture.muted,true);assert.equal(picture.loop,false);assert.equal(picture.plays,1);
 narration.currentTime=3;syncFinishedPicture({story,track,film:picture,narration,playing:false,force:true});assert.equal(picture.currentTime,3);assert.equal(picture.paused,true);
});
test('reduced motion steps through current facts and cannot reveal the following cue early',()=>{
 assert.ok(reducedFilmFrame(track,.5)<2.5);assert.ok(reducedFilmFrame(track,8.1)<9);
 assert.equal(reducedFilmFrame(track,9.1),10.6);assert.equal(reducedFilmFrame(track,11.9),10.6);
 const picture=film();syncFinishedPicture({story,track,film:picture,narration:{currentTime:9.1,playbackRate:1,paused:false},playing:true,reducedMotion:true});assert.equal(picture.paused,true);assert.equal(picture.currentTime,10.6);
});

test('reduced motion follows renderer word-bound picture cuts without exposing the next scene early',()=>{
 const authored={...track,pictureCues:[3.25,3.8,5.6,null,'7',NaN,-2,99]};
 // The existing 2.5s headline reveal cannot jump through the next authored cut.
 assert.equal(reducedFilmFrame(authored,3.249),3.249);
 // At the exact cue, step into the new scene, stopping before its next change.
 assert.equal(reducedFilmFrame(authored,3.25),3.799);
 assert.equal(reducedFilmFrame(authored,3.8),5.4);
 assert.equal(reducedFilmFrame({...track,pictureCues:{}},3),reducedFilmFrame(track,3));
});
test('film synchronization leaves accepted browser compositions untouched',()=>{
 const picture=film();assert.equal(syncFinishedPicture({story:{programme:{visualTreatment:'directed'}},track,film:picture,narration:{currentTime:12},playing:true}),false);assert.equal(picture.currentTime,0);assert.equal(picture.loop,true);assert.equal(picture.muted,false);
});
test('a waiting, starved or seeking narration stops future pictures; recovery rejoins its clock',()=>{
 const picture=film(),narration={currentTime:12.5,playbackRate:1,paused:false,readyState:4};
 const sync=options=>syncFinishedPicture({story,track,film:picture,narration,playing:true,...options});
 sync();assert.equal(picture.paused,false);
 picture.currentTime=13;sync({buffering:true,force:true});assert.equal(picture.paused,true);assert.equal(picture.currentTime,12.5);
 narration.readyState=2;sync();assert.equal(picture.paused,true);
 narration.readyState=4;narration.seeking=true;sync();assert.equal(picture.paused,true);
 narration.seeking=false;narration.currentTime=20;sync({force:true});assert.equal(picture.paused,false);assert.equal(picture.currentTime,20);
 narration.paused=true;sync();assert.equal(picture.paused,true);
});
test('selecting a finished story preserves its poster until the viewer actually starts playback',()=>{
 const picture=film();picture.currentTime=4;
 const narration={currentTime:0,playbackRate:1,paused:true,readyState:4};
 assert.equal(syncFinishedPicture({story,track,film:picture,narration,started:false,force:true}),true);
 assert.equal(picture.currentTime,4);assert.equal(picture.plays,0);assert.equal(picture.pauses,0);
 narration.paused=false;syncFinishedPicture({story,track,film:picture,narration,started:true,playing:true,force:true});
 assert.equal(picture.currentTime,0);assert.equal(picture.plays,1);
});
