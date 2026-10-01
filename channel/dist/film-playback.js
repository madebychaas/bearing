// Finished story pictures follow the existing narration clock and preferences.
export const isFinishedFilm=story=>story?.programme?.visualTreatment==='finished-film';
export function pictureSource(story,voice){return isFinishedFilm(story)?story.voices?.[voice]?.video:story?.video||story?.voices?.[voice]?.video;}
export function editionFamily(story){return isFinishedFilm(story)?'films.json':story?.format==='headline-video'?'latest-edition.json':'programmes.json';}
export function reducedFilmFrame(track,time){
 const pictureCues=Array.isArray(track.pictureCues)?track.pictureCues:[];
 const cues=[0,...(track.chapters||[]).map(c=>c.start),...(track.visualCues||[]).flatMap(c=>[c.start,...(c.reveals||[]).map(r=>r.start)]),...(track.openingCues||[]).map(c=>c.start),...(track.closingCues||[]).map(c=>c.start),...pictureCues].filter(cue=>Number.isFinite(cue)&&cue>=0&&cue<track.duration).sort((a,b)=>a-b);
 const unique=[...new Set(cues)],index=Math.max(0,unique.findLastIndex(cue=>cue<=time));
 // Jump once to the settled form of the current reveal, stopping before the
 // next authored cue. No later fact appears before its narration reference.
 return Math.max(0,Math.min(unique[index]+1.6,(unique[index+1]??track.duration)-.001,track.duration-.001));
}
export function syncFinishedPicture({story,track,film,narration,started=true,playing=false,reducedMotion=false,buffering=false,force=false}){
 if(!isFinishedFilm(story)||!track)return false;
 // Metadata and rate events fire while selecting a story. Seeking then would
 // replace its authored poster with the quiet first frame before Watch now.
 if(!started)return true;
 film.loop=false;film.muted=true;film.playbackRate=narration.playbackRate||1;
 const raw=reducedMotion?reducedFilmFrame(track,narration.currentTime||0):(narration.currentTime||0),time=Math.max(0,Math.min(raw,track.duration-.001));
 if(film.readyState>0&&(force||Math.abs(film.currentTime-time)>(reducedMotion?.001:.18)))film.currentTime=time;
 if(reducedMotion||!playing||buffering||narration.paused||narration.seeking||narration.readyState<3)film.pause();else if(film.paused)film.play().catch(()=>{});
 return true;
}
