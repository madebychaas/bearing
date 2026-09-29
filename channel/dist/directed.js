// Every visible fact follows the narration clock, including seeks and pauses.
import {US_STATES,US_VIEWBOX} from './us-states.js';
const clamp=n=>Math.max(0,Math.min(1,n));
const ease=n=>{const t=clamp(n);return t*t*(3-2*t);};
const node=(tag,cls,text)=>{const el=document.createElement(tag);el.className=cls;if(text!==undefined)el.textContent=text;return el;};
const svgNode=(tag,attrs={})=>{const el=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,String(v));return el;};
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
 let active='',items=[],statePaths=[],route=null,storyValue=null;
 function build(key,story,beat){
  active=key;surface.replaceChildren();items=[];statePaths=[];route=null;
  const kind=beat?.kind||key;surface.dataset.kind=kind;
  const composition=node('div','directed-composition');
  const context=story.programme.editorialTiming?.mode==='context-example';
  const kicker=kind==='lead'?(context?'IN FOCUS / CONTEXT':'IN FOCUS'):kind==='payoff'?'THE PAYOFF':beat?.label||'';
  composition.append(node('span','directed-kicker',kicker));
  const content=node('div','directed-content');composition.append(content);surface.append(composition);
  const reveals=kind==='lead'?story.programme.openingReveals:kind==='payoff'?story.programme.closingReveals:beat?.reveals;
  for(const [index,reveal] of (reveals||[]).entries()){
   const el=node('div','directed-reveal',reveal.text);el.dataset.role=reveal.role;el.style.setProperty('--reveal','0');
   content.append(el);items.push({el,index,role:reveal.role});
  }
  if(kind==='geography'){
   const map=svgNode('svg',{viewBox:US_VIEWBOX,class:'directed-map',role:'img','aria-label':'United States. States with award recipients: Florida, Kentucky, Virginia, New Mexico, Michigan, Ohio, Texas and Tennessee.'});
   for(const state of US_STATES){
    const selected=beat.states.includes(state.id),path=svgNode('path',{d:state.path,class:selected?'award-state':'base-state','fill-rule':'evenodd'});
    const title=svgNode('title');title.textContent=state.name;path.append(title);map.append(path);
    if(selected)statePaths.push(path);
   }
   const key=node('div','map-key','States with award recipients');key.prepend(node('i','map-swatch'));key.style.setProperty('--reveal','0');
   content.append(map,key);items.push({el:key,role:'geography',follows:'geography'});
  }
  if(kind==='mechanism'){
   route=svgNode('svg',{viewBox:'0 0 800 190',class:'mechanism-route','aria-hidden':'true',preserveAspectRatio:'none'});
   route.append(svgNode('path',{d:'M145 24 H655 M400 24 V104 M128 156 V104 H672 V156 M400 104 V156',pathLength:1}));
   content.prepend(route);
   for(const {el,role} of items){if(['internships','apprenticeships','projects'].includes(role)){const mark=node('span','practice-mark');mark.setAttribute('aria-hidden','true');el.prepend(mark);}}
  }
  if(kind==='lead'||kind==='payoff'){
   const graphic=svgNode('svg',{class:'orientation-route',viewBox:'0 0 760 120','aria-hidden':'true',preserveAspectRatio:'none'});
   graphic.append(svgNode('path',{d:'M2 65 H485 C525 65 530 22 575 22 H714',pathLength:1}),svgNode('circle',{cx:732,cy:22,r:15}));
   content.append(graphic);route=graphic;
  }
 }
 return {
  setStory(story){active='';storyValue=story;surface.replaceChildren();},
  draw(story,track,time,phase,prefs){
   const enabled=story?.programme.visualTreatment==='directed';canvas.hidden=!enabled;if(!enabled)return;
   const scene=phase==='story'?directedSceneAt(track,time):null,beat=scene?story.programme.beats[scene.beat]:null;
   const key=phase==='ident'||phase==='opening'?'lead':phase==='closing'||phase==='outro'?'payoff':beat?.kind||'lead';
   if(key!==active||story!==storyValue){storyValue=story;build(key,story,beat);}
   const chapter=track.chapters.find(c=>c.kind===(key==='lead'?'opening':key==='payoff'?'closing':'story'));
   const start=scene?.start??chapter?.start??0,enter=prefs.reducedMotion?1:ease(Math.max(0,time-start)/(.9*(prefs.pace||1)));
   surface.style.setProperty('--scene-enter',enter);
   surface.style.setProperty('--scene-exit',scene&&!prefs.reducedMotion?ease((scene.end-time)/(.35*(prefs.pace||1))):1);
   const cues=key==='lead'?track.openingCues:key==='payoff'?track.closingCues:scene?.reveals;
   const values=new Map();
   for(const item of items){
    const index=item.follows?items.find(x=>x.role===item.follows&&!x.follows)?.index:item.index;
    const cue=cues?.find(c=>c.reveal===index),poster=prefs.poster&&key==='lead',p=poster?1:cue?revealProgress(cue.start,time,prefs.pace,prefs.reducedMotion):0;
    item.el.style.setProperty('--reveal',p);item.el.setAttribute('aria-hidden',String(!poster&&(!cue||time<cue.start)));values.set(item.role,p);
   }
   for(const path of statePaths)path.style.setProperty('--highlight',values.get('geography')||0);
   route?.style.setProperty('--route',key==='mechanism'?(values.get('employer')||0):key==='lead'?(values.get('work')||0):(values.get('employment')||0));
   const media=courtesyAt(story,track,time,phase);courtesy.hidden=!media;
   if(media){courtesy.querySelector('.courtesy-name').textContent=media.courtesy;courtesy.querySelector('.courtesy-date').textContent=media.dateLabel||'';courtesy.title=`${media.author} · ${media.license}`;}
  }
 };
}
