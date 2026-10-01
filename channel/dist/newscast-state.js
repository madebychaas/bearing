import {validStory} from './playlist.js';

export const NEWSCAST_MIN=2, NEWSCAST_MAX=3;
export const ACTIVE_JOB_STATES=new Set(['queued','working']);
export const JOB_STATES=new Set([...ACTIVE_JOB_STATES,'needs_attention','failed','cancelled','interrupted','ready']);
export const defaultNewscastPreferences=()=>({voice:'warm',pace:'natural',music:'quiet'});
export function newscastPreferences(value={}){
 return {voice:value.voice==='measured'?'measured':'warm',pace:value.pace==='unhurried'?'unhurried':'natural',music:value.music==='off'?'off':'quiet'};
}
export function catalogStories(value,now=Date.now()){
 const ids=new Set();
 return (Array.isArray(value)?value:[]).filter(story=>{
  if(!story||typeof story.id!=='string'||!story.id||typeof story.revision!=='string'||!story.revision||typeof story.title!=='string'||typeof story.publisher!=='string'||!/^https:\/\//.test(story.sourceUrl||''))return false;
  const time=Date.parse(story.publishedAt);
  if(!Number.isFinite(time)||time>now+300000||ids.has(story.id))return false;
  ids.add(story.id);return true;
 }).sort((a,b)=>Date.parse(b.publishedAt)-Date.parse(a.publishedAt)||a.id.localeCompare(b.id));
}
export function toggleNewscastStory(selected,story){
 if(selected.some(item=>item.id===story.id))return {selected:selected.filter(item=>item.id!==story.id),message:''};
 if(selected.length>=NEWSCAST_MAX)return {selected,message:'Three is a good place to stop. Remove a story to choose another.'};
 return {selected:[...selected,{...story}],message:''};
}
export function selectionChanges(selected,catalog){
 const current=new Map(catalog.map(item=>[item.id,item]));
 return selected.filter(item=>!current.has(item.id)||current.get(item.id).revision!==item.revision).map(item=>item.id);
}
export function canMakeNewscast(selected,catalog,capabilities,busy=false){
 return !busy&&selected.length>=NEWSCAST_MIN&&selected.length<=NEWSCAST_MAX&&new Set(selected.map(item=>item.id)).size===selected.length&&!selectionChanges(selected,catalog).length;
}
export function newscastRequest(selected,preferences,requestId){
 if(selected.length<NEWSCAST_MIN||selected.length>NEWSCAST_MAX||new Set(selected.map(item=>item.id)).size!==selected.length)throw new Error('Choose two or three different stories.');
 return {stories:selected.map(({id,revision})=>({id,revision})),preferences:newscastPreferences(preferences),requestId};
}
export function readyNewscast(job,now=Date.now()){
 const result=job?.result,stories=result?.stories;
 if(job?.status!=='ready'||!Array.isArray(stories)||stories.length<NEWSCAST_MIN||stories.length>NEWSCAST_MAX)return null;
 if(typeof job.id!=='string'||!Array.isArray(job.stories)||job.stories.length!==stories.length)return null;
 if(stories.length!==job.total||!stories.every(story=>validStory(story)&&story.programme?.visualTreatment==='finished-film')||new Set(stories.map(story=>story.id)).size!==stories.length||new Set(stories.map(story=>story.source.url)).size!==stories.length)return null;
 if(stories.some(story=>!Number.isFinite(Date.parse(story.expiresAt))||Date.parse(story.expiresAt)<=now))return null;
 if(stories.some((story,index)=>{const chosen=job.stories[index],lineage=story.production?.newscast,approval=story.production?.selection;return !chosen||typeof chosen.id!=='string'||typeof chosen.revision!=='string'||lineage?.jobId!==job.id||lineage?.eventId!==chosen.id||lineage?.sourceRevision!==chosen.revision||approval?.eventId!==chosen.id||!approval?.approval;}))return null;
 if(typeof result.teaser!=='string'||!result.teaser.trim())return null;
 const preferences=newscastPreferences(job.preferences),pace=preferences.pace==='unhurried'?.92:1;
 const duration=stories.reduce((sum,story)=>sum+story.voices[preferences.voice].duration/pace,0)+(stories.length-1)*1.5;
 return {stories:structuredClone(stories),selection:job.stories.map(({id,revision})=>({id,revision})),preferences,duration,teaser:result.teaser.trim(),id:job.id};
}
export function personalQueue(stories,failed=new Set()){
 return stories.filter(story=>!failed.has(story.id));
}
export function nextPersonalStory(stories,currentId,failed=new Set()){
 const index=stories.findIndex(story=>story.id===currentId);
 return stories.slice(index+1).find(story=>!failed.has(story.id))||null;
}
export function playerNewscastPreferences(original,requested){
 const prefs=newscastPreferences(requested);
 return {...original,voice:prefs.voice,pace:prefs.pace==='unhurried'?.92:1,music:prefs.music==='off'?'off':'drift',musicVolume:.12,transitionSounds:prefs.music!=='off'};
}
export function jobIsActive(job){return ACTIVE_JOB_STATES.has(job?.status);}
export function stageLabel(stage){
 return {sourcing:'Checking the reporting',writing:'Finding the story',editing:'Refining every line',voicing:'Giving the story its voice',directing:'Planning the picture',creating_visuals:'Bringing the picture together',scoring:'Finding the right sound',assembling:'Putting it all together',checking:'Checking the finished newscast'}[stage]||'Preparing your newscast';
}
