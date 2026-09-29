import {curate} from './editorial.js';
import {selectRecent,changedReports,relativeTime,sourceHealth} from './live-news.js';
const $=id=>document.getElementById(id);
const make=(tag,className,text)=>{const el=document.createElement(tag);if(className)el.className=className;if(text!==undefined)el.textContent=text;return el;};
export function createLatest({topics,getTopics}){
 const desktop=matchMedia("(min-width:960px) and (min-height:650px)");
 let page=0;const pageSize=()=>innerHeight>=850?4:3;
 let items=[],pending=null,health=null,hours=24,limit=6,loaded=false,busy=false,lastSuccess=0,failed=false;
 const selectedTopics=()=> $('latest-interest').value==='all'?null:$('latest-interest').value==='following'?getTopics():[$('latest-interest').value];
 const selected=data=>curate(selectRecent(data,{hours,topics:selectedTopics()}),{limit:120});
 const valid=item=>item&&typeof item.id==='string'&&typeof item.title==='string'&&topics[item.topic]&&/^https:\/\//.test(item.source?.url||'')&&typeof item.source.name==='string';
 function updateStatus(){
  const state=sourceHealth(health);
  if(failed){state.label='Connection interrupted';state.state='offline';}
  $('live-connection').textContent=state.label;$('live-connection').dataset.state=state.state;
  if(health){
   const contacts=health.sources?.map(s=>s.lastSuccess).filter(Boolean).sort()||[];
   const recent=contacts.at(-1);
   $('live-health').textContent=`${health.healthy} / ${health.total} feeds available${recent?` · Source contact ${relativeTime(recent).toLowerCase()}`:''}`;
  }else $('live-health').textContent=failed?'Unable to reach the local news service.':'Checking the publishers…';
  const notice=state.state==='delayed'?'Source updates are delayed. Showing the last available reports with their original times.':failed?'The connection was interrupted. These are the last loaded reports.':state.state==='offline'?'Publishers are unavailable. Retained reports keep their original timestamps.':'';
  $('latest-notice').textContent=notice;$('latest-notice').hidden=!notice;
  for(const el of document.querySelectorAll('#latest-list time'))el.textContent=relativeTime(el.dateTime);
 }
 function render(){
  const list=$('latest-list');list.replaceChildren();const filtered=selected(items);
  $('latest-count').textContent=`${filtered.length} ${filtered.length===1?'report':'reports'} · U.S. impact first`;
  if(!filtered.length){list.append(make('p','latest-empty',loaded?'No reports match this time window and your interests. Try a wider window or All interests.':'The latest reports are not available yet. Check again in a moment.'));}
  page=Math.min(page,Math.max(0,Math.ceil(filtered.length/pageSize())-1));
  const visible=desktop.matches?filtered.slice(page*pageSize(),(page+1)*pageSize()):filtered.slice(0,limit);
  for(const [index,item] of visible.entries()){
   const article=make('article',`news-item${index===0?' lead-report':''}`);article.dataset.reportId=item.id;
   const meta=make('div','news-meta');const timestamp=make('time','',relativeTime(item.publishedTime));timestamp.dateTime=item.publishedTime;timestamp.title=`Published ${new Date(item.publishedTime).toLocaleString()}`;
   meta.append(make('span','news-publisher',item.source.name),make('span','news-category',item.topicLabel),timestamp);
   if(item.lastChangedAt)meta.append(make('span','report-updated','Updated'));if(item.sourceAvailable===false)meta.append(make('span','report-unavailable','Source delayed'));
   const heading=make('h3');const link=make('a','headline-link',item.title);link.href=item.source.url;link.target='_blank';link.rel='noopener noreferrer';heading.append(link);
   const action=make('a','news-source-link',`Read at ${item.source.name} ↗`);action.href=item.source.url;action.target='_blank';action.rel='noopener noreferrer';action.setAttribute('aria-label',`Read ${item.title} at ${item.source.name}`);
   article.append(meta,heading,action);list.append(article);
  }
  $('load-more-news').hidden=desktop.matches||filtered.length<=limit;
  $('reports-prev').disabled=page===0;$('reports-next').disabled=(page+1)*pageSize()>=filtered.length;
  $('reports-page').textContent=filtered.length?`${page*pageSize()+1}–${Math.min((page+1)*pageSize(),filtered.length)} of ${filtered.length}`:'No reports';
  updateStatus();
 }
 function showPending(){
  if(!pending){$('new-reports').hidden=true;return;}
  const count=changedReports(selected(items),selected(pending.items)).length;
  $('new-reports').textContent=count?`${count} ${count===1?'new or updated report':'new or updated reports'} ↑`:'Refresh this time window ↑';
  $('new-reports').hidden=!count;
 }
 function applyPending(){page=0;if(pending){items=pending.items;pending=null;}limit=6;render();showPending();}
 async function refresh({apply=false}={}){
  if(busy)return;busy=true;$('latest-refresh').disabled=true;
  const results=await Promise.allSettled(['reporting.json','source-status.json'].map(async url=>{const response=await fetch(url,{cache:'no-cache',signal:AbortSignal.timeout(8000)});if(!response.ok)throw new Error('News unavailable');return response.json();}));
  if(results[1].status==='fulfilled'&&Array.isArray(results[1].value.sources))health=results[1].value;
  const data=results[0].status==='fulfilled'?results[0].value:null;
  if(data&&Array.isArray(data.items)){
   const next={...data,items:data.items.filter(valid)};failed=results[1].status==='rejected';lastSuccess=Date.now();
   if(!loaded||apply){items=next.items;loaded=true;pending=null;render();}
   else if(changedReports(items,next.items).length||items.some(item=>!next.items.some(other=>other.id===item.id))){pending=next;}
   else {items=next.items;pending=null;}
  }else {failed=true;if(!loaded)render();}
  const visibleIds=new Set(selected(items).map(item=>item.id));
  if([...document.querySelectorAll('[data-report-id]')].some(el=>!visibleIds.has(el.dataset.reportId)))render();
  updateStatus();showPending();busy=false;$('latest-refresh').disabled=false;
 }
 for(const [value,label] of Object.entries(topics)){const option=make('option','',label);option.value=value;$('latest-interest').append(option);}
 $('latest-interest').onchange=()=>{applyPending();};
 $('new-reports').onclick=()=>{applyPending();$('latest-title').tabIndex=-1;$('latest-title').focus({preventScroll:true});};
 $('latest-refresh').onclick=()=>{page=0;refresh({apply:true});};
 $('reports-prev').onclick=()=>{page=Math.max(0,page-1);render();};$('reports-next').onclick=()=>{page++;render();};
 let resizeTimer;addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>render(),150);});
 $('load-more-news').onclick=()=>{limit+=18;render();};
 setInterval(()=>{if(!document.hidden){refresh();if(lastSuccess&&Date.now()-lastSuccess>90000)failed=true;updateStatus();}},30000);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
 refresh();
 return {preferencesChanged(){applyPending();},refresh};
}
