import {selectRecent,relativeTime} from './live-news.js';
import {createStudio} from './studio.js';
const $=id=>document.getElementById(id);
const make=(tag,cls,text)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;return el;};
const asset=value=>typeof value==='string'&&/^assets\/[a-zA-Z0-9_./-]+$/.test(value)&&!value.includes('..');
export const validClip=s=>s?.status==='ready'&&['studio-programme','headline-video'].includes(s.format)&&typeof s.id==='string'&&typeof s.title==='string'&&asset(s.image)&&/^https:\/\//.test(s.source?.url||'')&&(s.format==='headline-video'||s.programme&&asset(s.video))&&['warm','measured'].every(v=>asset(s.voices?.[v]?.audio||s.voices?.[v]?.video)&&s.voices[v].duration>1&&Array.isArray(s.voices[v].captions));
export function orderedClips(stories,filter){
 const groups=new Map();for(const story of selectRecent(stories,filter)){if(!groups.has(story.topic))groups.set(story.topic,[]);groups.get(story.topic).push(story);}
 const result=[];while(groups.size)for(const [topic,group] of groups){result.push(group.shift());if(!group.length)groups.delete(topic);}return result;
}
export function createBulletin({getPreferences,savePreferences,getFilter}){
 const film=$('bulletin-film'),music=$('bulletin-music'),audio=document.createElement('audio');audio.id='bulletin-narration';audio.preload='metadata';document.body.append(audio);film.muted=true;film.loop=true;
 let stories=[],pending=null,version='',current=null,voice='warm',seen=new Set(),failed=new Set(),active=false,wanted=false,started=false,request=0,resumeDialog=false;
 const key=s=>`${s.id}:${s.programmeVersion||s.mediaVersion}`;
 const list=()=>orderedClips(stories.filter(s=>!failed.has(key(s))),getFilter());
 const studio=createStudio({host:$('bulletin-player'),media:audio,music,getPreferences,getState:()=>({playing:wanted,started,muted:audio.muted}),getNextTitle:()=>list().find(s=>s.id!==current?.id&&!seen.has(key(s)))?.title||list().find(s=>s.id!==current?.id)?.title});
 function message(text){$('bulletin-message').textContent=text;$('bulletin-message').hidden=!text;}
 function controls(){
  const playing=wanted&&!audio.paused;
  $('bulletin-play').textContent=playing?'Ⅱ':'▶';$('bulletin-play').setAttribute('aria-label',playing?'Pause latest briefing':'Play latest briefing');
  $('bulletin-start').hidden=started||!current;$('bulletin-cc').setAttribute('aria-pressed',String(getPreferences().captions));
  $('bulletin-mute').textContent=audio.muted?'Muted':'Sound';$('bulletin-mute').setAttribute('aria-label',audio.muted?'Unmute headline audio':'Mute headline audio');
  $('bulletin-still').hidden=!current||!getPreferences().reducedMotion;
  if(getPreferences().reducedMotion)film.pause();else if(wanted&&active)film.play().catch(()=>{});studio.update();
 }
 function atmosphere(){
  const prefs=getPreferences();music.volume=prefs.musicVolume;music.muted=audio.muted;
  if(prefs.music==='off'||!wanted||!active){music.pause();return;}
  const src=`assets/music-${prefs.music}.mp3`;if(music.getAttribute('src')!==src){music.src=src;music.load();}music.play().catch(()=>{});
 }
 function pause(){wanted=false;request++;audio.pause();film.pause();music.pause();controls();}
 async function play(){
  if(!current||!active)return;
  if(!list().some(s=>key(s)===key(current))){advance();return;}
  const token=++request;wanted=true;started=true;message('');audio.playbackRate=getPreferences().pace;
  try{await audio.play();if(token!==request||!active||!wanted){if(!wanted||!active){audio.pause();film.pause();}return;}if(!getPreferences().reducedMotion)film.play().catch(()=>{});atmosphere();controls();}
  catch{if(token!==request)return;pause();message('Press Play to start the briefing.');}
 }
 function queue(){
  const available=list(),upcoming=available.filter(s=>s.id!==current?.id&&!seen.has(key(s)));
  if(upcoming.length<3)for(const s of available)if(s.id!==current?.id&&!upcoming.includes(s))upcoming.push(s);
  $('bulletin-count').textContent=`${available.length} stories`;
  const container=$('bulletin-queue');container.replaceChildren();
  for(const [index,story] of upcoming.slice(0,3).entries()){
   const button=make('button','bulletin-queue-item');button.setAttribute('aria-label',`Watch story: ${story.title}`);
   const copy=make('span','bulletin-queue-copy');copy.append(make('span','bulletin-queue-meta',`${story.topicLabel} · ${relativeTime(story.publishedTime)}`),make('span','bulletin-queue-title',story.title));
   button.append(make('span','bulletin-queue-number',String(index+1).padStart(2,'0')),copy);button.onclick=()=>load(story,true);container.append(button);
  }
  if(!upcoming.length)container.append(make('p','bulletin-queue-empty',available.length?'New clips join as they are ready.':'Choose another interest or a wider time window.'));
  $('bulletin-next').disabled=!available.length;
  $('bulletin-updates').textContent=pending?'A new programme is ready. It joins after this story.':'Continuous playlist · New stories join between segments.';
 }
 function empty(){
  pause();current=null;started=false;studio.setStory(null);audio.removeAttribute('src');audio.load();film.removeAttribute('src');film.removeAttribute('poster');film.load();
  $('bulletin-empty').hidden=false;$('bulletin-empty').textContent='No complete story matches this window yet. Try a wider window, or explore Watch. Fresh headlines remain below.';
  $('bulletin-start').disabled=true;$('bulletin-play').disabled=true;$('bulletin-start').hidden=true;$('bulletin-caption').hidden=true;$('bulletin-still').hidden=true;$('bulletin-original').hidden=true;
  $('bulletin-source').textContent='Your interests are saved.';$('bulletin-published').textContent='';$('bulletin-time').textContent='0:00 / 0:00';$('bulletin-seek').value=0;queue();
 }
 function load(story,autoplay=false){
  pause();current=story;voice=getPreferences().voice;started=false;seen.add(key(story));message('');
  audio.src=story.voices[voice].audio||story.voices[voice].video;audio.load();audio.playbackRate=getPreferences().pace;film.src=story.video||story.voices[voice].video;film.poster=story.image;film.load();$('bulletin-still').src=story.image;studio.setStory(story,voice);
  film.setAttribute('aria-label',story.title);$('bulletin-empty').hidden=true;$('bulletin-start').disabled=false;$('bulletin-play').disabled=false;
  $('bulletin-source').textContent=`${story.source.name} · ${story.topicLabel}`;$('bulletin-published').textContent=`Published ${relativeTime(story.publishedTime).toLowerCase()}${story.sourceAvailable===false?' · Source delayed':''}`;
  $('bulletin-published').title=new Date(story.publishedTime).toLocaleString();$('bulletin-original').href=story.source.url;$('bulletin-original').hidden=false;
  $('bulletin-player').dataset.storyId=story.id;$('bulletin-player').dataset.mediaVersion=story.programmeVersion||story.mediaVersion;queue();progress();controls();if(autoplay)play();
 }
 function applyPending(){if(!pending)return;stories=pending.stories;version=pending.version;pending=null;failed.clear();}
 function advance(){
  applyPending();const available=list();if(!available.length){empty();return;}
  let next=available.find(s=>!seen.has(key(s)));
  if(!next){seen.clear();next=available.find(s=>s.id!==current?.id)||available[0];}
  load(next,true);
 }
 function syncSelection(){
  applyPending();const available=list();
  if(!available.length){empty();return;}
  if(!current||audio.error||!available.some(s=>key(s)===key(current)))load(available[0],wanted&&active);
  queue();
 }
 function receive(edition){
  if(!edition||!Array.isArray(edition.stories))return;
  const incoming={...edition,stories:edition.stories.filter(validClip)};
  if(incoming.version===version||incoming.version===pending?.version){if(failed.size&&!wanted){failed.clear();syncSelection();}else queue();return;}
  pending=incoming;
  if(!wanted){syncSelection();}else queue();
 }
 const time=n=>`${Math.floor((n||0)/60)}:${String(Math.floor((n||0)%60)).padStart(2,'0')}`;
 function progress(){
  if(!current)return;const duration=Number.isFinite(audio.duration)?audio.duration:current.voices[voice].duration;
  $('bulletin-time').textContent=`${time(audio.currentTime)} / ${time(duration)}`;$('bulletin-seek').value=duration?audio.currentTime/duration*100:0;
  const caption=current.voices[voice].captions.find(c=>audio.currentTime>=c.start&&audio.currentTime<c.end);
  $('bulletin-caption').textContent=caption?.text||'';$('bulletin-caption').hidden=!getPreferences().captions||!started||!caption;
 }
 $('bulletin-start').onclick=play;$('bulletin-play').onclick=()=>wanted?pause():play();$('bulletin-next').onclick=advance;
 $('bulletin-seek').oninput=()=>{if(current&&Number.isFinite(audio.duration)){audio.currentTime=audio.duration*Number($('bulletin-seek').value)/100;progress();}};
 $('bulletin-mute').onclick=()=>{audio.muted=!audio.muted;music.muted=audio.muted;controls();};
 $('bulletin-cc').onclick=()=>{getPreferences().captions=!getPreferences().captions;savePreferences();progress();controls();};
 $('bulletin-fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('bulletin-player').requestFullscreen();}catch{message('Fullscreen is unavailable here. You can still watch in this view.');}};
 audio.addEventListener('timeupdate',progress);audio.addEventListener('loadedmetadata',progress);audio.addEventListener('play',controls);audio.addEventListener('pause',controls);
 audio.addEventListener('ended',()=>{if(wanted&&active)advance();});
 audio.addEventListener('error',()=>{if(!current||!audio.hasAttribute('src'))return;failed.add(key(current));pause();queue();message('This story is unavailable. Press Next for another story.');});
 music.addEventListener('error',()=>music.pause());
 document.addEventListener('keydown',e=>{if(!active||document.querySelector('dialog[open]')||/INPUT|TEXTAREA|SELECT|BUTTON|A/.test(e.target.tagName)||e.ctrlKey||e.altKey||e.metaKey)return;if(e.code==='Space'||e.key==='k'){e.preventDefault();wanted?pause():play();}else if(e.key==='ArrowRight'||e.key==='n'){e.preventDefault();advance();}});
 return {receive,pause,play,unavailable(){ $('bulletin-updates').textContent='Video updates unavailable. Retaining complete stories.';if(!current)$('bulletin-empty').textContent='Video is temporarily unavailable. Check again in a moment.';},filtersChanged:syncSelection,setActive(value){active=value;if(!active)pause();else if(!wanted)syncSelection();},preferencesChanged(){audio.playbackRate=getPreferences().pace;atmosphere();controls();progress();syncSelection();},openDialog(){resumeDialog=wanted;pause();},closeDialog(){if(resumeDialog&&active){resumeDialog=false;play();}else resumeDialog=false;}};
}
