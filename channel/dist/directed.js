// A story-directed treatment. Its reveals follow the narration clock, including seeks.
const clamp=n=>Math.max(0,Math.min(1,n));
const ease=n=>{const t=clamp(n);return t*t*(3-2*t);};
const node=(tag,cls,text)=>{const el=document.createElement(tag);el.className=cls;if(text!==undefined)el.textContent=text;return el;};
export function directedSceneAt(track,time){return track?.visualCues?.find(c=>time>=c.start&&time<c.end)||null;}
export function revealProgress(start,time,pace=1,reduced=false){return time<start?0:reduced?1:ease((time-start)/(.65*pace));}
export function courtesyAt(story,track,time,phase){
 if(phase!=='story')return null;
 const scene=directedSceneAt(track,time),media=scene&&story.programme.beats[scene.beat]?.media;
 return media?.usageApproved&&media.courtesy?media:null;
}
export function createDirected(root){
 const canvas=node('div','directed-canvas'),surface=node('div','directed-scene');
 const courtesy=node('div','directed-courtesy');courtesy.append(node('span','courtesy-label','COURTESY'),node('span','courtesy-name'),node('span','courtesy-date'));
 canvas.append(surface,courtesy);root.append(canvas);
 let active=null,items=[],photo=null,closingItems=[];
 function build(beat){
  surface.replaceChildren();items=[];photo=null;surface.dataset.kind=beat?.kind||'';
  if(!beat)return;
  if(beat.media){photo=node('img','directed-photo');photo.src=beat.media.src;photo.alt=beat.media.alt||'';surface.append(photo,node('div','directed-photo-shade'));}
  const composition=node('div','directed-composition');composition.append(node('span','directed-kicker',beat.label));
  const content=node('div','directed-content');
  for(const [index,reveal] of (beat.reveals||[]).entries()){
   const el=node('div','directed-reveal',reveal.text);el.dataset.role=reveal.role;el.style.setProperty('--reveal','0');
   if(beat.kind==='investment'&&reveal.role==='scope'){
    const marks=node('span','directed-awards');marks.setAttribute('aria-hidden','true');
    for(let i=0;i<9;i++)marks.append(node('i','award-mark'));
    el.append(marks);
   }
   content.append(el);items.push({el,index});
  }
  composition.append(content);surface.append(composition);
 }
 return {
  setStory(story,closing){
   active=null;build(null);closing.querySelector('.directed-outcomes')?.remove();closingItems=[];
   if(story?.programme.visualTreatment!=='directed')return;
   const outcomes=node('div','directed-outcomes');
   for(const [index,reveal] of (story.programme.closingReveals||[]).entries()){
    const el=node('div','directed-outcome',reveal.text);el.dataset.role=reveal.role;outcomes.append(el);closingItems.push({el,index});
   }
   closing.append(outcomes);
  },
  draw(story,track,time,phase,prefs){
   const enabled=story?.programme.visualTreatment==='directed';canvas.hidden=!enabled;if(!enabled)return;
   const scene=phase==='story'?directedSceneAt(track,time):null;
   const beat=scene?story.programme.beats[scene.beat]:null;
   if(beat!==active){active=beat;build(beat);}
   surface.hidden=!scene;
   if(scene){
    const elapsed=time-scene.start;
    // Keep the current subject legible until its narration ends; the next subject enters over 1.5s.
    surface.style.setProperty('--scene-enter',prefs.reducedMotion?1:ease(elapsed/(1.5*(prefs.pace||1))));
    surface.style.setProperty('--photo-scale',prefs.reducedMotion?1:1.035-.035*clamp(elapsed/(scene.end-scene.start)));
    for(const {el,index} of items){
     const cue=scene.reveals?.find(c=>c.reveal===index);const progress=cue?revealProgress(cue.start,time,prefs.pace,prefs.reducedMotion):0;
     el.style.setProperty('--reveal',progress);el.setAttribute('aria-hidden',String(!cue||time<cue.start));
    }
   }
   const media=courtesyAt(story,track,time,phase);courtesy.hidden=!media;
   if(media){courtesy.querySelector('.courtesy-name').textContent=media.courtesy;courtesy.querySelector('.courtesy-date').textContent=media.dateLabel||'';courtesy.title=`${media.author} · ${media.license}`;}
   for(const {el,index} of closingItems){
    const cue=track.closingCues?.find(c=>c.reveal===index);const p=phase==='closing'&&cue?revealProgress(cue.start,time,prefs.pace,prefs.reducedMotion):0;
    el.style.setProperty('--reveal',p);el.setAttribute('aria-hidden',String(!p));
   }
  }
 };
}
