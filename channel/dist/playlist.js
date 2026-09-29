import {curate} from './editorial.js';
import {balancedRotation} from './rotation.js';
import {publicationTime} from './live-news.js';

const asset=value=>typeof value==='string'&&/^assets\/[a-zA-Z0-9_./-]+$/.test(value)&&!value.includes('..');
export const franchise=story=>story.format==='headline-video'?{name:'The Brief',note:'The latest, in brief',tone:'brief'}:story.topic==='nature'?{name:'Field Notes',note:'Our changing planet',tone:'field'}:{name:'In Focus',note:'A story worth understanding',tone:'focus'};
export function validStory(s){
 if(!s||s.status!=='ready'||typeof s.id!=='string'||typeof s.title!=='string'||!asset(s.image)||!/^https:\/\//.test(s.source?.url||''))return false;
 const brief=s.format==='headline-video';
 if(!brief&&(!s.programme||s.visual?.scope!=='story'||s.visual.storyId!==s.id||!asset(s.video)))return false;
 return ['warm','measured'].every(v=>s.voices?.[v]&&asset(brief?s.voices[v].video:s.voices[v].audio)&&Array.isArray(s.voices[v].captions)&&s.voices[v].duration>1);
}
export function mergeEditions(editions){
 const stories=editions.flatMap(e=>e?.stories||[]).filter(validStory),seen=new Set();
 // A full presentation supersedes its short headline, without playing the report twice.
 return stories.sort((a,b)=>(a.format==='headline-video')-(b.format==='headline-video')).filter(s=>{
  if(seen.has(s.id)||seen.has(s.source.url))return false;seen.add(s.id);seen.add(s.source.url);return true;
 });
}
export function selectPlaylist(stories,{topics,series='all',cycle=0,failed=new Set(),now=Date.now()}={}){
 const fresh=stories.filter(s=>(!topics||topics.includes(s.topic))&&!failed.has(s.id)&&(!s.expiresAt||Date.parse(s.expiresAt)>now)&&(s.format!=='headline-video'||Number.isFinite(publicationTime(s))&&publicationTime(s)<=now&&now-publicationTime(s)<86400000)&&(series==='all'||franchise(s).tone===series));
 if(fresh.some(s=>s.editorial))return curate(fresh,{limit:24,cycle});
 const byDate=(a,b)=>(publicationTime(b)||0)-(publicationTime(a)||0);
 const features=balancedRotation(fresh.filter(s=>s.format!=='headline-video').sort(byDate),cycle);
 const briefs=balancedRotation(fresh.filter(s=>s.format==='headline-video').sort(byDate),cycle);
 // Open with a produced story, then keep two fresh updates between features.
 const queue=[];
 while(features.length||briefs.length){if(features.length)queue.push(features.shift());queue.push(...briefs.splice(0,2));}
 return queue;
}
