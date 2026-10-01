import {relativeTime} from './live-news.js';
import {catalogStories,toggleNewscastStory,selectionChanges,canMakeNewscast,newscastRequest,newscastPreferences,defaultNewscastPreferences,readyNewscast,jobIsActive,stageLabel,JOB_STATES} from './newscast-state.js';

const el=(tag,className,text)=>{const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;};
const button=(className,text,action)=>{const node=el('button',className,text);node.type='button';node.dataset.newscastAction=text.toLowerCase().replace(/[^a-z0-9]+/g,'-');node.addEventListener('click',action);return node;};
const storageKey='bearing.newscast.job.v1';
const durationLabel=seconds=>{const whole=Math.round(seconds);return `${Math.floor(whole/60)}:${String(whole%60).padStart(2,'0')}`;};
const errorText=(error,fallback)=>typeof error?.message==='string'?error.message:fallback;

export function createNewscast({trigger,onOpen=()=>{},onClose=()=>{},onLaunch=()=>{},onReturn=()=>{}}){
 let catalog=[],capabilities={},selected=[],preferences=defaultNewscastPreferences(),job=null,completion=null,view='choose',loading=false,submitting=false,connectionLost=false,catalogFailed=false,notice='',pollTimer=null,polling=false,requestId=null,closeIntent='browse',requestRevision=0;
 const dialog=el('dialog','newscast-dialog');dialog.id='newscast-dialog';dialog.setAttribute('aria-labelledby','newscast-title');
 const header=el('header','newscast-header'),heading=el('div'),title=el('h2','','Make my newscast'),intro=el('p','newscast-intro','Choose two or three stories. Get the context that matters.');title.id='newscast-title';
 const close=button('newscast-close','×',()=>dialog.close());close.setAttribute('aria-label','Close newscast');heading.append(title,intro);header.append(heading,close);
 const body=el('div','newscast-body'),live=el('p','newscast-announcement');live.setAttribute('role','status');live.setAttribute('aria-live','polite');live.setAttribute('aria-atomic','true');
 dialog.append(header,body,live);document.body.append(dialog);
 function announce(message){if(live.textContent!==message)live.textContent=message;}
 function remember(){try{if(job?.id)localStorage.setItem(storageKey,job.id);else localStorage.removeItem(storageKey);}catch{}}
 function updateTrigger(){
  trigger.dataset.state=connectionLost?'attention':job?.status||'idle';
  trigger.textContent=connectionLost?'Check my newscast':job?.status==='ready'?'My newscast is ready':jobIsActive(job)?'Making my newscast':job&&['failed','needs_attention','interrupted'].includes(job.status)?'Check my newscast':'Make my newscast';
 }
 function show(){if(!dialog.open){closeIntent='browse';onOpen();dialog.showModal();}render();if(view==='choose'&&!loading)void loadCatalog();}
 function currentResult(){return readyNewscast(view==='complete'?{status:'ready',id:completion?.id,total:completion?.stories.length,stories:completion?.selection,preferences:completion?.preferences,result:completion}:job);}
 function launch(){const ready=currentResult();if(!ready){notice='These stories are no longer current or their delivery could not be verified. Choose current stories to continue.';render();return;}closeIntent='launch';dialog.close();onLaunch(ready);}
 function returnToChannel(){closeIntent='return';dialog.close();onReturn();}
 function startAgain(){
  job=null;remember();connectionLost=false;view='choose';selected=[];requestId=null;notice='';clearTimeout(pollTimer);render();void loadCatalog();
 }
 async function api(path,{method='GET',data}={}){
  const response=await fetch(path,{method,cache:'no-store',headers:data?{'Content-Type':'application/json'}:undefined,body:data?JSON.stringify(data):undefined,signal:AbortSignal.timeout(20000)});
  let value;try{value=await response.json();}catch{throw Object.assign(new Error('The news service could not be reached. Try again.'),{status:response.status});}
  if(!response.ok)throw Object.assign(new Error(typeof value.message==='string'?value.message:typeof value.error==='string'?value.error:'The news service could not complete that request.'),{status:response.status});
  return value;
 }
 async function loadCatalog(){
  if(loading)return;loading=true;catalogFailed=false;render();
  try{const value=await api('/api/newscast/catalog');catalog=catalogStories(value.stories);capabilities=value.capabilities||{};catalogFailed=false;}
  catch(error){catalogFailed=true;notice=errorText(error,'The latest reporting is temporarily unavailable.');}
  finally{loading=false;if(view==='choose')render();}
 }
 function adoptJob(value){
  if(!value||typeof value.id!=='string'||!JOB_STATES.has(value.status))throw new Error('The production status could not be read. Try again.');
  job=value;remember();connectionLost=false;notice='';if(view!=='complete')view='job';updateTrigger();render();
  announce(job.status==='ready'?'Your newscast is ready.':job.message||stageLabel(job.stage));
 }
 function schedulePoll(){clearTimeout(pollTimer);if(jobIsActive(job))pollTimer=setTimeout(()=>void pollJob(),3000);}
 async function pollJob(){
  if(!job?.id||polling)return;polling=true;const id=job.id,revision=requestRevision;
  try{const value=await api(`/api/newscasts/${encodeURIComponent(id)}`);if(revision===requestRevision&&job?.id===id)adoptJob(value.job);}
  catch(error){if(revision!==requestRevision||job?.id!==id)return;connectionLost=true;notice=errorText(error,'Connection interrupted. Your newscast may still be in production.');updateTrigger();render();announce('Connection interrupted. Check the newscast status to continue.');}
  finally{polling=false;if(!connectionLost)schedulePoll();}
 }
 async function submit(){
  if(!canMakeNewscast(selected,catalog,capabilities,submitting||loading||catalogFailed))return;
  submitting=true;notice='';requestId??=crypto.randomUUID();render();
  try{const value=await api('/api/newscasts',{method:'POST',data:newscastRequest(selected,preferences,requestId)});requestRevision++;adoptJob(value.job);schedulePoll();}
  catch(error){notice=error.status===409?'The reporting changed. Review the marked stories and choose their updated versions before making your newscast.':errorText(error,'Your newscast could not be started. Try again.');if(error.status===409){requestId=null;await loadCatalog();}announce(notice);}
  finally{submitting=false;render();}
 }
 async function cancel(){
  if(!job?.id||submitting)return;submitting=true;render();
  try{const value=await api(`/api/newscasts/${encodeURIComponent(job.id)}/cancel`,{method:'POST',data:{}});requestRevision++;adoptJob(value.job);schedulePoll();}
  catch(error){notice=errorText(error,'Cancellation could not be confirmed. Check the status before trying again.');connectionLost=true;updateTrigger();}
  finally{submitting=false;render();}
 }
 async function retry(){
  if(!job?.id||submitting)return;submitting=true;notice='';render();
  try{const value=await api(`/api/newscasts/${encodeURIComponent(job.id)}/retry`,{method:'POST',data:{}});requestRevision++;adoptJob(value.job);schedulePoll();}
  catch(error){notice=error.status===409?'The reporting changed. Choose the updated stories to continue.':errorText(error,'Production could not resume. Your choices are preserved.');}
  finally{submitting=false;render();}
 }
 function parameter(name,label,choices){
  const field=el('fieldset','newscast-parameter'),legend=el('legend','',label),options=el('div','newscast-options');field.append(legend,options);
  for(const [value,text] of choices){const option=button('',text,()=>{preferences={...preferences,[name]:value};requestId=null;render();body.querySelector(`[data-newscast-choice="${name}-${value}"]`)?.focus({preventScroll:true});});option.dataset.newscastChoice=`${name}-${value}`;option.setAttribute('aria-pressed',String(preferences[name]===value));options.append(option);}
  return field;
 }
 function renderSelection(){
  title.textContent='Make my newscast';intro.textContent='Choose two or three stories. Get the context that matters.';
  const grid=el('div','newscast-choose'),news=el('section','newscast-news'),newsTop=el('div','newscast-list-heading'),newsTitle=el('h3','','Latest reporting'),refresh=button('newscast-text-button',loading?'Updating…':'Refresh',()=>{notice='';void loadCatalog();});refresh.disabled=loading;newsTop.append(newsTitle,refresh);
  const list=el('div','newscast-reports');list.setAttribute('aria-label','Latest stories to choose');const changed=new Set(selectionChanges(selected,catalog));
  if(loading&&!catalog.length)list.append(el('p','newscast-empty','Checking the latest reporting…'));
  else if(!catalog.length)list.append(el('p','newscast-empty',catalogFailed?'Reporting is unavailable right now. Try refreshing.':'No current stories are available from the connected sources. Check again shortly.'));
  for(const story of catalog){
   const row=el('article','newscast-report'),label=el('label','newscast-report-choice'),input=el('input');input.type='checkbox';input.checked=selected.some(item=>item.id===story.id);input.id=`newscast-story-${catalog.indexOf(story)}`;
   input.setAttribute('aria-label',story.title);
   input.disabled=!input.checked&&selected.length>=3;input.addEventListener('change',()=>{const result=toggleNewscastStory(selected,story);selected=result.selected;notice=result.message;requestId=null;const scroll=list.scrollTop;render();body.querySelector('.newscast-reports').scrollTop=scroll;body.querySelector(`#${input.id}`)?.focus({preventScroll:true});announce(`${selected.length} of three stories selected.`);});
   const copy=el('span','newscast-report-copy'),meta=el('span','newscast-report-meta'),time=el('time','',relativeTime(story.publishedAt));time.dateTime=story.publishedAt;time.title=new Date(story.publishedAt).toLocaleString();meta.append(el('span','',story.publisher),time);
   copy.append(meta,el('strong','newscast-report-title',story.title));if(changed.has(story.id))copy.append(el('span','newscast-changed','Updated since you selected it. Remove and choose again.'));
   label.append(input,copy);const source=el('a','newscast-original','Read original ↗');source.href=story.sourceUrl;source.target='_blank';source.rel='noopener noreferrer';source.setAttribute('aria-label',`Read ${story.title} at ${story.publisher}`);row.append(label,source);list.append(row);
  }
  news.append(newsTop,list);
  const options=el('aside','newscast-settings'),chosen=el('div','newscast-selected'),count=el('h3','',`${selected.length} of 3 stories`);chosen.append(count);
  if(!selected.length)chosen.append(el('p','newscast-help','Pick the stories you want to understand. Your selection becomes the running order.'));
  selected.forEach((story,index)=>{const item=el('div','newscast-selected-item');item.append(el('span','newscast-selected-number',String(index+1).padStart(2,'0')),el('span','',story.title));const remove=button('newscast-remove','×',()=>{selected=selected.filter(value=>value.id!==story.id);requestId=null;render();announce(`${selected.length} of three stories selected.`);});remove.setAttribute('aria-label',`Remove ${story.title}`);item.append(remove);chosen.append(item);if(changed.has(story.id))chosen.append(el('p','newscast-changed',catalog.some(value=>value.id===story.id)?'This story changed. Choose its updated version.':'This story is no longer available. Choose another.'));});
  options.append(chosen,parameter('voice','Voice',[['warm','Warm'],['measured','Measured']]),parameter('pace','Delivery',[['natural','Natural'],['unhurried','Unhurried']]),parameter('music','Sound',[['quiet','Editorial score'],['off','Voice only']]));
  grid.append(news,options);body.append(grid);
  const footer=el('div','newscast-footer'),copy=el('div');
  if(!capabilities.generationReady&&!loading){copy.append(el('p','newscast-capability','Automatic story production needs a connection.'),el('p','newscast-help','Your choices can be saved now. We’ll keep them ready until production is available.'));}
  else copy.append(el('p','newscast-help',selected.length<2?'Choose at least two stories to continue.':changed.size?'Review your changed selections.':'Made to understand. Ready when every story is finished.'));
  const make=button('newscast-primary',submitting?'Starting…':'Make my newscast',()=>void submit());make.disabled=!canMakeNewscast(selected,catalog,capabilities,loading||submitting||catalogFailed);footer.append(copy,make);body.append(footer);
 }
 function jobCanvas(complete=false){
  const canvas=el('div','newscast-canvas');canvas.dataset.moving=String(!complete&&jobIsActive(job)&&!connectionLost&&!submitting);
  const art=el('div','newscast-orbit');art.setAttribute('aria-hidden','true');art.append(el('span','newscast-orbit-line'),el('span','newscast-orbit-line'),el('span','newscast-orbit-core'));
  const items=el('ol','newscast-story-stack');
  for(const story of (complete?completion?.stories:job?.stories)||[]){const item=el('li','newscast-stack-story');item.dataset.state=story.status||'waiting';item.append(el('span','newscast-stack-dot'),el('span','',story.title||'Selected story'));if(['ready','complete','completed'].includes(story.status))item.append(el('span','newscast-story-ready','Finished'));items.append(item);}
  canvas.append(art,items);return canvas;
 }
 function renderJob(){
  const complete=view==='complete',ready=currentResult(),active=!complete&&jobIsActive(job),stopped=connectionLost||!active;
  title.textContent=complete?completion?.playbackIssue?'Your newscast has ended.':'Your bearings, in hand.':ready?'Your newscast is ready.':connectionLost?'Let’s reconnect.':active?'Coming into focus.':job?.status==='cancelled'?'Production cancelled.':'A little attention is needed.';
  intro.textContent=complete?completion?.playbackIssue||'Replay your selected stories or return to the channel.':ready?ready.teaser:connectionLost?'Your production may still be running. Check its status to continue.':active?'We’re shaping your choices into something worth watching.':job?.message||'Your selection is preserved. We won’t send unfinished stories to the player.';
  const stage=el('section','newscast-job');stage.append(jobCanvas(complete));
  const details=el('div','newscast-job-details');
  if(ready){details.append(el('p','newscast-ready-meta',`${ready.stories.length} stories · ${durationLabel(ready.duration)} · ${ready.preferences.voice==='warm'?'Warm':'Measured'} voice`));}
  else if(active&&!connectionLost){details.append(el('h3','',stageLabel(job.stage)),el('p','newscast-help',job.message||'Your stories are being produced.'),el('p','newscast-count',`${Math.min(Number(job.completed)||0,Number(job.total)||0)} of ${Number(job.total)||selected.length} stories finished`));}
  else if(!connectionLost&&job?.error&&job.error!==job.message)details.append(el('p','newscast-help',typeof job.error==='string'?job.error:job.error.message||'Production could not finish.'));
  if((job?.status==='ready'||complete)&&!ready)details.append(el('p','newscast-help','These stories are no longer current or their delivery could not be verified. Choose current stories to continue.'));
  stage.append(details);body.append(stage);
  const footer=el('div','newscast-footer newscast-job-actions');
  if(ready){footer.append(button('newscast-text-button',complete?'Back to channel':'Choose another newscast',complete?returnToChannel:startAgain),button('newscast-primary',complete?'Replay my newscast':'Play my newscast',launch));}
  else if(active&&!connectionLost){const cancelButton=button('newscast-text-button',submitting?'Cancelling…':'Cancel production',()=>void cancel());cancelButton.disabled=submitting;footer.append(cancelButton,button('newscast-secondary','Keep browsing',()=>dialog.close()));}
  else {const retryButton=button('newscast-primary',connectionLost?'Check status':['needs_attention','failed','interrupted'].includes(job?.status)?'Try production again':'Refresh status',()=>{if(connectionLost){notice='';void pollJob();}else if(['needs_attention','failed','interrupted'].includes(job?.status))void retry();else void pollJob();});retryButton.disabled=submitting;footer.append(button('newscast-text-button',connectionLost&&jobIsActive(job)?'Keep browsing':'Choose stories',connectionLost&&jobIsActive(job)?()=>dialog.close():startAgain),retryButton);}
  body.append(footer);dialog.dataset.working=String(!stopped);
 }
 function render(){
  if(!dialog.open)return;
  const focused=document.activeElement,focusKey=focused?.dataset.newscastChoice,actionKey=focused?.dataset.newscastAction;body.replaceChildren();dialog.dataset.view=view;
  if(view==='choose')renderSelection();else renderJob();
  if(notice){const note=el('p','newscast-notice',notice);note.setAttribute('role','status');body.append(note);}
  if(focusKey)body.querySelector(`[data-newscast-choice="${focusKey}"]`)?.focus({preventScroll:true});
  else if(actionKey)body.querySelector(`[data-newscast-action="${actionKey}"]`)?.focus({preventScroll:true});
 }
 trigger.addEventListener('click',()=>{if(view==='complete'&&jobIsActive(job))view='job';show();});
 dialog.addEventListener('close',()=>{if(closeIntent==='browse')onClose();closeIntent='browse';});
 dialog.addEventListener('click',event=>{if(event.target===dialog){const bounds=dialog.getBoundingClientRect();if(event.clientX<bounds.left||event.clientX>bounds.right||event.clientY<bounds.top||event.clientY>bounds.bottom)dialog.close();}});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden&&jobIsActive(job)&&!connectionLost)void pollJob();});
 try{const id=localStorage.getItem(storageKey);if(id&&/^[\w-]{1,160}$/.test(id)){job={id,status:'interrupted',message:'Checking your saved newscast.'};connectionLost=true;view='job';updateTrigger();void pollJob();}}catch{}
 return {open:show,completed(result){completion=structuredClone(result);view='complete';show();},clearCompletion(){if(view==='complete')view=job?'job':'choose';},get job(){return job;}};
}
