import {franchise} from './playlist.js';
export const TRANSITION_SECONDS=1.5;
const ease=value=>{const t=Math.max(0,Math.min(1,value));return t*t*(3-2*t);};
const create=(tag,cls,text)=>{const node=document.createElement(tag);node.className=cls;if(text!==undefined)node.textContent=text;return node;};
export function phaseAt(chapters,time){return chapters?.find(c=>time>=c.start&&time<c.end)||chapters?.at(-1)||null;}
export function createStudio({host,media,music,getPreferences,getState,getNextTitle=()=>''}){
 const root=create('div','studio-layer');root.hidden=true;
 const ident=create('div','studio-ident');ident.append(create('span','studio-ident-kicker','YOUR WORLD. IN CONTEXT.'),create('strong','studio-wordmark','Bearing'),create('span','studio-ident-rule'),create('span','studio-ident-topic'));
 const card=create('div','studio-opening'),eyebrow=create('div','studio-eyebrow'),title=create('h2','studio-title'),why=create('p','studio-why');card.append(eyebrow,title,create('span','studio-why-label','WHY IT MATTERS'),why);
 const closing=create('div','studio-closing'),summary=create('h2','studio-summary'),outlook=create('p','studio-outlook');closing.append(create('span','studio-eyebrow','THE TAKEAWAY'),summary,create('span','studio-why-label','WHAT TO WATCH'),outlook);
 const beat=create('div','studio-beat'),beatLabel=create('span','studio-beat-label'),beatText=create('strong','studio-beat-text');beat.append(beatLabel,beatText);
 const outro=create('div','studio-outro'),nextTitle=create('h2','studio-next-title');outro.append(create('span','studio-eyebrow','UP NEXT'),nextTitle);
 const wipe=create('div','studio-wipe'),credit=create('div','studio-credit');root.append(ident,card,closing,beat,outro,credit,wipe);host.append(root);host.classList.add('studio-player');
 const rail=create('div','studio-chapters');host.append(rail);
 const sounds=Object.fromEntries(['ident','sweep','resolve'].map(name=>{const audio=new Audio(`assets/studio/${name}-v2.wav`);audio.preload='auto';audio.dataset.studioSound=name;audio.setAttribute('aria-hidden','true');host.append(audio);return [name,audio];}));
 let story=null,track=null,frame=0,lastTime=0,lastKind='',previousPlaying=false,seeked=false;
 const stopEffects=()=>{for(const sound of Object.values(sounds)){sound.pause();if(sound.currentTime)sound.currentTime=0;}};
 function cue(name){const prefs=getPreferences(),state=getState();if(prefs.transitionSounds===false||state.muted||!state.playing)return;stopEffects();const sound=sounds[name];sound.volume=.55;sound.playbackRate=1;sound.play().catch(()=>{});host.dataset.soundCue=name;}
 function draw(){
  frame=0;if(!story||!track){root.hidden=true;rail.hidden=true;return;}
  const state=getState(),prefs=getPreferences(),time=media.currentTime||0,chapter=phaseAt(track.chapters,time);if(!chapter)return;
  const kind=state.started?chapter.kind:'opening',elapsed=Math.max(0,time-chapter.start),remaining=chapter.end-time;
  root.hidden=false;rail.hidden=false;root.dataset.phase=kind;host.dataset.phase=kind;host.dataset.programme=story.programmeVersion;
  for(const [element,visible] of [[ident,kind==='ident'],[card,kind==='opening'],[closing,kind==='closing'],[beat,kind==='story'],[outro,kind==='outro']])element.setAttribute('aria-hidden',String(!visible));
  const transition=TRANSITION_SECONDS*(prefs.pace||1),enter=prefs.reducedMotion?1:ease(elapsed/transition),leave=prefs.reducedMotion?1:ease(remaining/transition);
  root.style.setProperty('--studio-enter',state.started?enter:1);root.style.setProperty('--studio-exit',state.started?leave:1);root.style.setProperty('--studio-travel',`${prefs.reducedMotion?0:Math.max(0,1-enter)*18}px`);root.style.setProperty('--studio-wipe',String(state.started&&!prefs.reducedMotion?1-ease(elapsed/transition):0));
  const brand=franchise(story);ident.querySelector('.studio-wordmark').textContent=brand.name;ident.querySelector('.studio-ident-kicker').textContent='BEARING / '+story.topicLabel.toUpperCase();ident.querySelector('.studio-ident-topic').textContent=brand.note;credit.textContent=`${story.source.name}  /  ${story.dateLabel||new Date(story.publishedTime).toLocaleDateString()}  /  AI ILLUSTRATION`;nextTitle.textContent=getNextTitle()||'More from your interests';
  const body=track.chapters.find(c=>c.kind==='story'),position=body?Math.max(0,Math.min(.999,(time-body.start)/(body.end-body.start))):0,b=story.programme.beats[Math.floor(position*story.programme.beats.length)];beatLabel.textContent=b.label;beatText.textContent=b.text;
  const beatLength=body?(body.end-body.start)/story.programme.beats.length:1,beatElapsed=body?(time-body.start)%beatLength:0;root.style.setProperty('--beat-opacity',prefs.reducedMotion?1:Math.min(ease(beatElapsed/transition),ease((beatLength-beatElapsed)/transition)));root.style.setProperty('--beat-travel',`${prefs.reducedMotion?0:12*(1-ease(beatElapsed/transition))}px`);
  for(const button of rail.children){const c=track.chapters[Number(button.dataset.chapter)];button.setAttribute('aria-current',String(c.kind===chapter.kind));button.style.setProperty('--chapter-progress',`${Math.max(0,Math.min(1,(time-c.start)/(c.end-c.start)))*100}%`);}
  const justStarted=state.playing&&!previousPlaying;
  if(state.playing&&state.started&&!seeked&&((kind!==lastKind&&time>=lastTime&&time-lastTime<.8)||(justStarted&&time<.25))){if(kind==='ident')cue('ident');else if(kind==='opening'||kind==='story'||kind==='closing')cue('sweep');else if(kind==='outro')cue('resolve');}
  if(!state.playing||state.muted||prefs.transitionSounds===false)stopEffects();
  if(music){const speech=track.captions.some(c=>time>=c.start-.15&&time<c.end+.2),desired=state.playing&&prefs.music!=='off'&&!state.muted?(prefs.musicVolume||0)*(speech?.28:.85):0;music.volume+=Math.max(-.015,Math.min(.015,desired-music.volume));music.muted=!!state.muted;}
  lastKind=kind;lastTime=time;previousPlaying=state.playing;seeked=false;if(state.playing)frame=requestAnimationFrame(draw);
 }
 function update(){if(frame)cancelAnimationFrame(frame);draw();}
 media.addEventListener('seeking',()=>{seeked=true;stopEffects();});media.addEventListener('seeked',update);media.addEventListener('timeupdate',()=>{if(!frame)update();});media.addEventListener('pause',()=>{stopEffects();update();});media.addEventListener('play',update);
 return {update,stopEffects,setStory(value,voice){stopEffects();story=value?.programme?value:null;host.classList.toggle('studio-player',!!story);track=story?.voices[voice];lastKind='';lastTime=0;previousPlaying=false;rail.replaceChildren();if(!story){root.hidden=true;rail.hidden=true;return;}title.textContent=story.title;eyebrow.textContent=`${franchise(story).name} / ${story.topicLabel}`.toUpperCase();why.textContent=story.programme.why;summary.textContent=story.programme.summary;outlook.textContent=story.programme.lookAhead;
  for(const [index,chapter] of track.chapters.entries()){if(chapter.kind==='ident'||chapter.kind==='outro')continue;const button=create('button','studio-chapter',chapter.label);button.dataset.chapter=index;button.setAttribute('aria-label',`Jump to ${chapter.label.toLowerCase()}`);button.onclick=()=>{seeked=true;media.currentTime=chapter.start;update();};rail.append(button);}update();},get phase(){return phaseAt(track?.chapters,media.currentTime||0)?.kind;}};
}
