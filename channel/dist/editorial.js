// Scores are produced from documented, nonpartisan rules in production/editorial.py.
export function curate(items,{limit=32,cycle=0}={}){
 if(!items.some(s=>s.editorial))return items.slice(0,limit);
 const seen=new Set();
 const available=items.filter(s=>s.editorial&&!s.editorial.suppressed&&!s.editorial.foreignLocal).sort((a,b)=>(a.format==='headline-video')-(b.format==='headline-video')||b.editorial.score-a.editorial.score).filter(s=>{const key=s.coverage?.id||s.id;if(seen.has(key))return false;seen.add(key);return true;});
 const byImpact=(a,b)=>b.editorial.score-a.editorial.score||Date.parse(b.publishedTime||b.publishedAt||0)-Date.parse(a.publishedTime||a.publishedAt||0);
 const domestic=available.filter(s=>s.editorial.domestic).sort(byImpact),foreign=available.filter(s=>!s.editorial.domestic&&!s.editorial.foreignLocal).sort(byImpact);
 const chosen=[],counts={};
 // Rotate only after an entire lap, keeping the first edition consequence-led.
 if(cycle&&domestic.length>limit){const offset=(cycle*limit)%domestic.length;domestic.push(...domestic.splice(0,offset));}
 while(domestic.length&&chosen.length<limit){
  let best=0;
  if(!cycle)for(let i=1;i<domestic.length;i++)if(domestic[i].editorial.score-(counts[domestic[i].editorial.publisher]||0)*18>domestic[best].editorial.score-(counts[domestic[best].editorial.publisher]||0)*18)best=i;
  const item=domestic.splice(best,1)[0];chosen.push(item);const publisher=item.editorial.publisher;counts[publisher]=(counts[publisher]||0)+1;
 }
 const international=Math.min(Math.floor(limit/10),Math.floor(chosen.length/9),foreign.length);
 return international?[...chosen.slice(0,limit-international),...foreign.slice(0,international)]:chosen;
}
