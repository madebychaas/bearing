// Publication time determines recency. Fetch time never makes an old report new.
export function publicationTime(item){
 const value=item?.publishedTime;
 if(typeof value!=='string'||!value.includes('T')||!/(Z|[+-]\d\d:\d\d)$/.test(value))return NaN;
 return Date.parse(value);
}
export function selectRecent(items,{hours=24,topics=null,now=Date.now()}={}){
 const seen=new Set();
 return items.filter(item=>{
  const time=publicationTime(item);
  if(!Number.isFinite(time)||time>now||now-time>hours*3600000||topics&&!topics.includes(item.topic))return false;
  if(seen.has(item.source.url))return false;seen.add(item.source.url);return true;
 }).sort((a,b)=>publicationTime(b)-publicationTime(a)||a.id.localeCompare(b.id));
}
export function changedReports(previous,next){
 const old=new Map(previous.map(item=>[item.id,item]));
 return next.filter(item=>{const prior=old.get(item.id);return !prior||prior.version!==item.version||prior.title!==item.title||prior.publishedTime!==item.publishedTime||JSON.stringify(prior.coverage)!==JSON.stringify(item.coverage)||JSON.stringify(prior.editorial)!==JSON.stringify(item.editorial);});
}
export function relativeTime(value,now=Date.now()){
 const ms=Date.parse(value);if(!Number.isFinite(ms))return 'Time unavailable';
 const minutes=Math.max(0,Math.floor((now-ms)/60000));
 if(minutes<1)return 'Just now';if(minutes<60)return `${minutes} min ago`;
 const hours=Math.floor(minutes/60);if(hours<24)return `${hours} ${hours===1?'hour':'hours'} ago`;
 return new Date(ms).toLocaleDateString(undefined,{month:'short',day:'numeric'});
}
export function sourceHealth(status,now=Date.now()){
 const checked=Date.parse(status?.checkedAt);
 if(!Number.isFinite(checked)||checked>now+300000||now-checked>180000)return {label:'Updates delayed',state:'delayed'};
 if(!status.healthy)return {label:'Sources unavailable',state:'offline'};
 if(status.healthy<status.total)return {label:'Some sources delayed',state:'partial'};
 return {label:'Auto-updating',state:'healthy'};
}
