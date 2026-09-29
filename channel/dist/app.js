import {createCameras} from './cameras.js';
import {franchise, mergeEditions, selectPlaylist} from './playlist.js';
import { createLatest } from './latest.js';
import { createStudio } from './studio.js';
const $ = id => document.getElementById(id);
let cameraController=null;
const audio = $('narration'), film = $('film'), music = $('music');
const topicNames={space:'Space & discovery',nature:'Nature & our planet',culture:'Art & culture',world:'U.S. & policy',technology:'Technology',business:'Money & economy',health:'Health',sport:'Sport',local:'North Texas'};
const defaults = {topics:Object.keys(topicNames).filter(t=>t!=='local'),pace:1,voice:'warm',music:'drift',musicVolume:.12,captions:true,transitionSounds:true,reducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches};
let preferences = {...defaults}, stories = [], current = null, playing = false, started = false, captions = [], voiceForStory = 'warm', switching = false, resumeAfterDialog = false, failedIds = new Set(), lastRefresh=0, pendingEdition=null, editionVersion='', refreshing=null, rotationCycle=0, series="all", playRevision=0, advancing=false, transitionTimer=null;
try { const saved=JSON.parse(localStorage.getItem('current.preferences.v1')); if(saved && typeof saved==='object') preferences={...defaults,...saved}; } catch {}
preferences.topics=Array.isArray(preferences.topics)?preferences.topics.filter(t=>topicNames[t]):[...defaults.topics];
if(!preferences.topics.length) preferences.topics=[...defaults.topics];
if(![.85,1,1.15].includes(preferences.pace)) preferences.pace=1;
if(!['warm','measured'].includes(preferences.voice)) preferences.voice='warm';
if(!['off','drift','piano'].includes(preferences.music)) preferences.music='off';
preferences.musicVolume=Math.max(0,Math.min(.35,Number(preferences.musicVolume)||0));
const formatTime=seconds=>`${Math.floor((seconds||0)/60).toString().padStart(2,'0')}:${Math.floor((seconds||0)%60).toString().padStart(2,'0')}`;
const eligible=(cycle=rotationCycle)=>selectPlaylist(stories,{topics:preferences.topics,series,cycle,failed:failedIds});
const displayTitle=story=>story.displayTitle||story.title;
const studio=createStudio({host:$('player'),media:audio,music,getPreferences:()=>preferences,getState:()=>({playing,started,muted:audio.muted}),getNextTitle:()=>{const list=eligible();return displayTitle(list[(list.findIndex(s=>s.id===current?.id)+1)%list.length]||{});}});
const upcomingMedia=document.createElement('audio');upcomingMedia.preload='metadata';
function prepareNext(){const list=eligible();const index=list.findIndex(s=>s.id===current?.id);const candidate=list[(index+1)%list.length];const track=candidate?.voices[preferences.voice];const url=track?.audio||track?.video;if(url&&candidate.id!==current?.id&&upcomingMedia.getAttribute('src')!==url){upcomingMedia.src=url;upcomingMedia.load();}}
const transitionSound=new Audio('assets/studio/sweep-v2.wav');
function cancelTransition(){clearTimeout(transitionTimer);transitionTimer=null;$('channel-transition').classList.remove('active');transitionSound.pause();}
function node(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function storePreferences(){try{localStorage.setItem('current.preferences.v1',JSON.stringify(preferences));}catch{}latest.preferencesChanged();}
function message(text){$('player-message').textContent=text;$('player-message').hidden=!text;}
function editionMetadata(edition){const date=new Date(`${edition.edition}T12:00:00Z`);if(!Number.isFinite(date.getTime()))return;$('edition-date').textContent=`EDITION / ${date.toLocaleDateString('en-US',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}).toUpperCase()}`;$('freshness').textContent=`Edition ${date.toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'UTC'})} · AI-produced presentation`;}
function emptySelection(){pause();current=null;started=false;studio.setStory(null);$('brief-design').hidden=true;film.removeAttribute('src');film.removeAttribute('poster');film.load();$('story-title').textContent='A little space for what interests you.';$('story-dek').textContent='No videos match this programme and your interests yet. The latest reporting is still beside you.';$('story-byline').textContent='YOUR CHANNEL';$('topic-label').textContent='YOUR INTERESTS';$('selection-reason').textContent='Your preferences are saved. No unrelated stories will play.';$('start').disabled=true;$('play').disabled=true;$('sources').disabled=true;$('caption').hidden=true;$('story-insight').hidden=true;message('');renderRotation();updateTransport();}
function renderRotation(){
 const rotation=$('rotation');rotation.replaceChildren();const list=eligible();
 if(!list.length)rotation.append(node('p','empty-rotation','No videos match this selection. Choose another programme or tune your interests.'));
 $('queue-count').textContent=`${list.length} videos`;
 for(const [index,story] of list.entries()){
  const now=story.id===current?.id,brand=franchise(story),card=node('button',`story-card${now?' active':''}`);card.dataset.storyId=story.id;card.dataset.series=brand.tone;
  card.setAttribute('aria-label',`Play ${displayTitle(story)}`);card.setAttribute('aria-current',String(now));
  const thumb=node('span','card-thumbnail'),image=node('img');image.src=story.image;image.alt='';image.loading='lazy';
  thumb.append(image,node('span','card-duration',formatTime(story.voices[preferences.voice].duration/preferences.pace)));
  const copy=node('span','card-copy');copy.append(node('span','card-category',brand.name),node('span','card-title',displayTitle(story)),node('span','card-source',story.source.name));
  card.append(node('span','card-index',now?'NOW PLAYING':String(index+1).padStart(2,'0')),thumb,copy);
  card.onclick=()=>switchStory(story);rotation.append(card);
 }
 prepareNext();
 $('rotation-meta').textContent=`${list.length} stories selected for you`;
 if(current)$('start-duration').textContent=`${formatTime(current.voices[preferences.voice].duration/preferences.pace)} · ${franchise(current).name.toUpperCase()}`;
}
function updateMotion(){document.body.classList.toggle('reduced-motion',!!preferences.reducedMotion);if(preferences.reducedMotion)film.pause();else if(playing)film.play().catch(()=>{});}
function renderPreferences(){
 const list=$('topic-options');list.replaceChildren();for(const [topic,label] of Object.entries(topicNames)){
  const button=node('button','topic-option',label);button.type='button';button.setAttribute('aria-pressed',String(preferences.topics.includes(topic)));
  button.onclick=()=>{if(preferences.topics.includes(topic)){if(preferences.topics.length===1){$('preference-note').textContent='Keep at least one interest in your channel.';return;}preferences.topics=preferences.topics.filter(t=>t!==topic);}else preferences.topics.push(topic);rotationCycle=0;storePreferences();renderPreferences();renderRotation();};list.append(button);
 }
 for(const key of ['pace','voice','music'])document.querySelectorAll(`[data-${key}]`).forEach(button=>{button.setAttribute('aria-pressed',String(String(preferences[key])===button.dataset[key]));button.onclick=()=>{preferences[key]=key==='pace'?Number(button.dataset[key]):button.dataset[key];if(key==='pace')audio.playbackRate=preferences.pace;if(key==='music')configureMusic();storePreferences();renderPreferences();renderRotation();};});
 $('transition-sounds').checked=preferences.transitionSounds!==false;$('music-volume').value=preferences.musicVolume;$('reduce-motion').checked=preferences.reducedMotion;
 $('preference-note').textContent='Your chosen interests and voice start with the next story. Pace and atmosphere change immediately. Saved on this device.';
}
function configureMusic(){
 if(preferences.music==='off'){music.pause();return;}
 const desired=current?.music?.[preferences.music]||`assets/music-${preferences.music}.mp3`;if(music.getAttribute('src')!==desired){music.src=desired;music.load();}
 music.volume=current?.programme?.soundTreatment==='editorial-score'?0:preferences.musicVolume;music.playbackRate=current?.programme?.soundTreatment==='editorial-score'?audio.playbackRate:1;if(playing)music.play().catch(()=>{});
}
function updateTransport(){
 $('play').textContent=playing?'Ⅱ':'▶';$('play').setAttribute('aria-label',playing?'Pause channel':'Play channel');
 $('full-play').textContent=playing?'Pause':'Play';
 $('player').classList.toggle('playing',started);$('story-intro').hidden=started;$('on-air-title').hidden=!started;$('caption').hidden=!started||!preferences.captions||!captions.length;
 $('captions').setAttribute('aria-pressed',String(preferences.captions));$('sound').setAttribute('aria-label',audio.muted?'Unmute narration':'Mute narration');$('sound').style.opacity=audio.muted?'.45':'1';
 music.muted=audio.muted;transitionSound.muted=audio.muted;if(preferences.transitionSounds===false)transitionSound.pause();studio.update();
}
function pause(){cancelTransition();playRevision++;playing=false;audio.pause();film.pause();music.pause();updateTransport();}
async function play(){
 if(!current||switching)return;cameraController?.stop();const revision=++playRevision;message('');started=true;playing=true;updateTransport();
 try{audio.playbackRate=preferences.pace;await audio.play();if(!playing||revision!==playRevision)return;if(!preferences.reducedMotion)film.play().catch(()=>{});configureMusic();}catch{if(revision===playRevision){pause();message('Playback needs a tap. Press Play to try again.');}}
}
function loadStory(story,autoplay=false){
 if(!story)return;switching=true;pause();current=story;started=false;voiceForStory=preferences.voice;const track=story.voices[voiceForStory];captions=track.captions;
 $('start').disabled=false;$('play').disabled=false;$('sources').disabled=false;
 audio.src=track.audio||track.video;audio.defaultPlaybackRate=preferences.pace;audio.load();audio.playbackRate=preferences.pace;film.src=story.video||track.video;film.poster=story.image;film.loop=story.format!=='headline-video';film.muted=true;film.load();
 const brand=franchise(story);$('player').dataset.storyId=story.id;$('player').dataset.series=brand.tone;$('programme-name').textContent=brand.name;$('programme-note').textContent=brand.note;
 $('brief-design').hidden=story.format!=='headline-video';$('brief-design').dataset.long=String(story.title.length>170);$('brief-title').textContent=story.title;$('brief-source').textContent=story.source.name;$('brief-topic').textContent=story.topicLabel;
 $('topic-label').textContent=story.topicLabel.toUpperCase();$('story-byline').textContent=`${story.source.name} · ${story.dateLabel||new Date(story.publishedTime).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})}`.toUpperCase();$('story-title').textContent=displayTitle(story);$('story-dek').textContent=story.programme?.why||story.displayDek||story.dek||'A quick, attributed headline. Read the original report for the full context.';
 $('on-air-title').textContent=displayTitle(story);$('selection-reason').textContent=story.editorial?.focus!=='general'&&story.editorial?.reason?story.editorial.reason:`For your interest in ${story.topicLabel.toLowerCase()}`;$('story-insight').hidden=true;
 film.setAttribute('aria-label',story.visual?.alt||'AI-illustrated story');document.querySelector('.visual-label').textContent=story.format==='headline-video'?'HEADLINE GRAPHIC':'AI ILLUSTRATION';document.querySelector('.visual-label').title=story.visualDisclosure;
 studio.setStory(story,voiceForStory);
 $('time').textContent=`00:00 / ${formatTime(track.duration)}`;$('seek').value=0;message('');switching=false;renderRotation();updateTransport();if(autoplay)play();
}
function switchStory(story){
 if(!story)return;const animate=started&&!preferences.reducedMotion;pause();
 if(!animate){loadStory(story,true);return;}
 const overlay=$('channel-transition');$('transition-series').textContent=franchise(story).name;overlay.classList.add('active');
 if(preferences.transitionSounds!==false&&!audio.muted){const scored=current?.programme?.soundTreatment==='editorial-score'?current:story.programme?.soundTreatment==='editorial-score'?story:null;transitionSound.src=scored?(scored.music.bridge||scored.music.handoff):'assets/studio/sweep-v2.wav';transitionSound.currentTime=0;transitionSound.volume=scored?.55:.35;transitionSound.play().catch(()=>{});}
 transitionTimer=setTimeout(()=>{overlay.classList.remove('active');transitionTimer=null;loadStory(story,true);},1500);
}
async function next(){
 if(advancing)return;advancing=true;
 try{void refreshEdition();applyPending();let list=eligible();if(!list.length){emptySelection();return;}const index=list.findIndex(s=>s.id===current?.id);if(index===list.length-1){rotationCycle++;list=eligible();switchStory(list[0]);}else switchStory(list[index+1]);}finally{advancing=false;}
}
function applyPending(){if(!pendingEdition)return;stories=pendingEdition.stories;editionVersion=pendingEdition.version;editionMetadata(pendingEdition);pendingEdition=null;failedIds.clear();$('update-status').textContent='New arrivals are in your playlist.';renderRotation();}
async function fetchEditions(){
 const results=await Promise.allSettled(['programmes.json','latest-edition.json'].map(async url=>{const response=await fetch(url,{cache:'no-cache',signal:AbortSignal.timeout(8000)});if(!response.ok)throw new Error('Edition unavailable');const data=await response.json();if(!Array.isArray(data.stories))throw new Error('Invalid edition');return data;}));
 if(results.every(result=>result.status==='rejected'))throw new Error('Editions unavailable');
 // Keep the last playable part if only one edition could be reached.
 const editions=results.map((result,i)=>result.status==='fulfilled'?result.value:{stories:stories.filter(s=>(s.format==='headline-video')===(i===1)),version:`retained-${i}`});
 return {stories:mergeEditions(editions),version:editions.map(e=>e.version||e.builtAt).join(':'),edition:editions[0].edition||new Date().toISOString().slice(0,10)};
}
async function refreshEdition(){
 if(refreshing)return refreshing;if(Date.now()-lastRefresh<30000)return;lastRefresh=Date.now();
 refreshing=(async()=>{try{const data=await fetchEditions();if(data.version===editionVersion)return;pendingEdition=data;$('update-status').textContent='New arrivals will join after this story.';if(!current){applyPending();if(eligible().length)loadStory(eligible()[0]);}}catch{$('update-status').textContent='Updates are temporarily unavailable. Your loaded playlist is still here.';}finally{refreshing=null;}})();return refreshing;
}
function progress(){
 if(!current)return;const duration=Number.isFinite(audio.duration)?audio.duration:current.voices[voiceForStory].duration;const time=audio.currentTime;const ratio=duration?time/duration:0;
 $('time').textContent=`${formatTime(time)} / ${formatTime(duration)}`;$('seek').value=ratio*100;
 const caption=captions.find(c=>time>=c.start&&time<c.end);$('caption').textContent=caption?.text||'';$('caption').hidden=!preferences.captions||!started||!caption;
 if(current.format==='headline-video'){if(!preferences.reducedMotion&&Math.abs(film.currentTime-time)>.4)film.currentTime=time;if(preferences.music!=='off')music.volume=preferences.musicVolume*(caption?.28:.85);}
 const index=Math.min(2,Math.floor(ratio*3));const fact=current.facts?.[index];$('story-insight').hidden=!started||!fact||ratio<.09||ratio>.89;if(fact)$('insight-text').textContent=fact;
}
function openDialog(dialog){resumeAfterDialog=playing;pause();dialog.showModal();}
function sourceView(){
 if(!current)return;const panel=$('source-content');panel.replaceChildren();
 const link=node('a','source-article');link.href=current.source.url;link.target='_blank';link.rel='noopener noreferrer';link.append(node('span','',`${current.source.name} · ${current.dateLabel||new Date(current.publishedTime).toLocaleString()}`),node('strong','',`${current.source.title} ↗`));
 panel.append(link);
 const media=[...new Map((current.programme?.beats||[]).filter(b=>b.media).map(b=>[b.media.src,b.media])).values()];
 if(media.length){panel.append(node('p','source-label','VISUAL CREDITS'));for(const item of media){
  const credit=node('p','source-description',`${item.title||'File photograph'} · ${item.author}. ${item.dateLabel||''}. `);
  const original=node('a','', item.kind==='map'?'Map source':'Original photograph');original.href=item.sourceUrl;original.target='_blank';original.rel='noopener noreferrer';
  const license=node('a','',item.license);license.href=item.licenseUrl;license.target='_blank';license.rel='noopener noreferrer';
  credit.append(original,document.createTextNode(' · '),license,document.createTextNode(`. ${item.displayChanges||''}`));panel.append(credit);
 }}
 const coverage=current.coverage;if(coverage?.sources?.length>1){panel.append(node('p','source-label','RELATED COVERAGE'));panel.append(node('p','source-description','Reports grouped by headline similarity. This does not imply independent confirmation.'));for(const source of coverage.sources){if(source.url===current.source.url)continue;const related=node('a','source-article',`${source.name}: ${source.title} ↗`);related.href=source.url;related.target='_blank';related.rel='noopener noreferrer';panel.append(related);}}
 panel.append(node('p','source-description',current.editorialNote||'This short update reads the publisher headline with attribution. Follow the source for the complete reporting.'),node('p','source-label','HOW THIS SEGMENT WAS MADE'),node('p','source-description',current.visualDisclosure||'AI-produced presentation based on linked reporting; not live footage.'),node('p','source-label','NARRATION'),node('p','source-script',current.script));openDialog($('source-dialog'));
}
$('start').onclick=play;$('play').onclick=()=>playing?pause():play();$('next').onclick=next;
$('full-play').onclick=()=>playing?pause():play();$('full-next').onclick=next;$('full-exit').onclick=()=>document.exitFullscreen().catch(()=>{});
$('seek').oninput=()=>{if(Number.isFinite(audio.duration)){audio.currentTime=audio.duration*Number($('seek').value)/100;progress();}};
$('captions').onclick=()=>{preferences.captions=!preferences.captions;storePreferences();updateTransport();progress();};
$('sound').onclick=()=>{audio.muted=!audio.muted;updateTransport();};
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('player').requestFullscreen();}catch{message('Fullscreen is unavailable in this browser. You can still watch here.');}};
$('tune').onclick=()=>{renderPreferences();openDialog($('preferences'));};
$('save-preferences').onclick=()=>{if(!current&&eligible().length)loadStory(eligible()[0]);$('preferences').close();};$('sources').onclick=sourceView;$('close-sources').onclick=()=>$('source-dialog').close();
$('playlist-series').onchange=()=>{series=$('playlist-series').value;rotationCycle=0;renderRotation();if(!current||!eligible().some(s=>s.id===current.id)){const wasPlaying=playing;const story=eligible()[0];if(story)loadStory(story,wasPlaying);else emptySelection();}};
for(const dialog of document.querySelectorAll('dialog')){dialog.addEventListener('close',()=>{if(resumeAfterDialog){resumeAfterDialog=false;play();}});dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});}
$('music-volume').oninput=()=>{preferences.musicVolume=Number($('music-volume').value);music.volume=preferences.musicVolume;storePreferences();};
$('transition-sounds').onchange=()=>{preferences.transitionSounds=$('transition-sounds').checked;studio.update();storePreferences();};
$('reduce-motion').onchange=()=>{preferences.reducedMotion=$('reduce-motion').checked;updateMotion();storePreferences();};
audio.addEventListener('timeupdate',progress);audio.addEventListener('loadedmetadata',progress);audio.addEventListener('ended',next);
audio.addEventListener('error',()=>{if(!current||switching)return;const continuePlaying=playing;failedIds.add(current.id);pause();renderRotation();if(continuePlaying&&eligible().length){message('This story is unavailable. Moving to the next.');next();}else message('This story’s audio is unavailable. Press Next for another story.');});
film.addEventListener('error',()=>{if(current&&film.hasAttribute('src')){film.removeAttribute('src');film.load();}});
music.addEventListener('error',()=>{music.pause();preferences.music='off';storePreferences();});
document.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]')||e.target.closest('#rotation')||/INPUT|TEXTAREA|SELECT|BUTTON|A/.test(e.target.tagName)||e.ctrlKey||e.altKey||e.metaKey)return;if(e.code==='Space'||e.key==='k'){e.preventDefault();playing?pause():play();}else if(e.key==='ArrowRight'||e.key==='n'){e.preventDefault();next();}else if(e.key==='ArrowLeft'&&current){audio.currentTime=0;progress();}});
async function boot(){
 try{const edition=await fetchEditions();stories=edition.stories;editionVersion=edition.version;editionMetadata(edition);renderPreferences();updateMotion();configureMusic();if(eligible().length)loadStory(eligible()[0]);else emptySelection();}
 catch{message('This edition isn’t available yet. Please reload in a moment.');$('start').disabled=true;$('play').disabled=true;}
}
const latest=createLatest({topics:topicNames,getTopics:()=>preferences.topics});
createCameras({onOpen:pause}).then(controller=>{cameraController=controller;});
boot();
setInterval(()=>{if(!document.hidden)refreshEdition();},30000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshEdition();});
