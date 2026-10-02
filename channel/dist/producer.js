const PAGE_SIZE=8;
const productNames={brief:'The Brief',focus:'In Focus'};
const actionNames={none:'Not yet reviewed',shortlist:'Shortlisted',watch:'Watching',dismiss:'Dismissed',reset:'Returned to candidates'};
const nationalScopes=new Set(['national','world-impact']);
const assignmentLanes={today:'Today’s lead',developing:'Developing',watch:'Watch',held:'Held for review'};

export function candidateFilters(snapshot){
 return snapshot?.assignment?[['today','Today’s leads'],['developing','Developing'],['watch','Watch'],['all','All national'],['shortlist','Shortlist'],['alternatives','Held / out of scope'],['dismissed','Dismissed']]:[['all','Top candidates'],['updates','Meaningful updates'],['watch','Watch'],['local','Local signals'],['shortlist','Shortlist'],['alternatives','Alternatives / held'],['dismissed','Dismissed']];
}
export function discoveryLag(value){
 if(!Number.isFinite(value)||value<0)return 'Not measured';
 if(value<1)return 'Under 1 min';
 if(value<60)return `${Math.round(value)} min`;
 return `${(value/60).toFixed(1)} hr`;
}
export function assignmentPegSource(event){
 const sourceId=event.assignment?.todayPeg?.sourceId;
 return sourceId?(event.evidence||[]).find(source=>source.id===sourceId)||null:null;
}
export function sourceClockLabel(source){return source?.sourceTimeKind==='filed'?'Filed':source?.sourceTimeKind==='updated'?'Updated':'Published';}
export function assignmentReportClock(event){
 const source=assignmentPegSource(event);
 return source?{label:sourceClockLabel(source),at:source.publishedAt||null}:{label:'Source time',at:null};
}

export function safeSourceURL(value){
 try{const url=new URL(value);return ['http:','https:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null;}catch{return null;}
}
export function rankedCandidates(snapshot,product='brief',filter='all'){
 const events=new Map((snapshot?.events||[]).map(event=>[event.id,event]));
 const ranked=(snapshot?.rankings?.[product]||[]).map(id=>events.get(id)).filter(Boolean);
 // Live assignment signals prioritize the desk; product rank breaks equal-priority ties.
 if(snapshot?.assignment)ranked.sort((a,b)=>(Number(b.assignment?.priority)||0)-(Number(a.assignment?.priority)||0));
 return ranked.filter(event=>{
  const action=event.decision?.action||'none';
  if(filter==='dismissed')return action==='dismiss';
  if(snapshot?.assignment){
   const desk=event.assignment||{},national=nationalScopes.has(desk.scope);
   if(filter==='shortlist')return action==='shortlist';
   if(action==='dismiss')return false;
   if(filter==='alternatives')return desk.lane==='held'||!national;
   if(!national)return false;
   if(['today','developing','watch'].includes(filter))return desk.lane===filter;
   return true;
  }
  if(filter==='updates')return !!event.signals?.update;
  if(filter==='watch')return action!=='dismiss'&&(action==='watch'||!!event.signals?.watch);
  if(filter==='local')return action!=='dismiss'&&!!event.localSignal;
  if(filter==='shortlist')return action==='shortlist';
  if(filter==='alternatives')return action!=='dismiss'&&event.eligible===false;
  return action!=='dismiss'&&event.eligible!==false;
 });
}
export function candidatePage(snapshot,product,filter,page=0){
 const all=rankedCandidates(snapshot,product,filter),pages=Math.max(1,Math.ceil(all.length/PAGE_SIZE));
 const current=Math.max(0,Math.min(pages-1,Number.isFinite(page)?Math.floor(page):0));
 return {items:all.slice(current*PAGE_SIZE,(current+1)*PAGE_SIZE),total:all.length,page:current,pages,start:all.length?current*PAGE_SIZE+1:0,end:Math.min(all.length,(current+1)*PAGE_SIZE)};
}
export function relativeTime(value,asOf=new Date().toISOString()){
 const minutes=(Date.parse(asOf)-Date.parse(value))/60000;
 if(!Number.isFinite(minutes))return 'Time unverified';
 if(minutes< -5)return 'Future-dated';
 if(minutes<1)return 'Just now';
 if(minutes<60)return `${Math.floor(minutes)}m ago`;
 if(minutes<1440)return `${Math.floor(minutes/60)}h ago`;
 return `${Math.floor(minutes/1440)}d ago`;
}
export function freshnessLabel(event){return ({stale:'Older reporting',future:'Future-dated',unknown:'Time unverified'})[event.whyNow?.status]||'';}
export function readableReportingText(value){return String(value||'').replace(/\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\b/g,stamp=>{const time=new Date(stamp);return Number.isFinite(time.getTime())?time.toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):stamp;});}
export function localSignalSources(snapshot,signal){
 const reports=new Map();for(const event of snapshot?.events||[])for(const source of event.evidence||[])if(!reports.has(source.id))reports.set(source.id,{...source,eventId:event.id});
 const ids=[...new Set(signal?.reportIds||[])];return {reports:ids.map(id=>reports.get(id)).filter(Boolean),missingIds:ids.filter(id=>!reports.has(id))};
}

export function handoffActions(selection,{dirty=false,busy=false,actor='',reviewed=false}={}){
 const blocked=!!selection?.reassessment?.required||selection?.state==='needs-reassessment';
 const running=selection?.state==='producing'||selection?.production?.state==='running';
 const idle=!!selection&&!busy&&!running;
 return {save:idle&&!blocked,review:!!selection&&!busy&&!dirty&&!!actor.trim(),approve:idle&&!dirty&&!blocked&&!!actor.trim()&&reviewed&&!!selection?.draft&&!!selection?.prepared&&!selection?.draft?.issues?.length,
  reassess:idle&&!dirty&&blocked,produce:idle&&!dirty&&!blocked&&selection?.state==='approved'&&!!selection?.approval};
}
export function handoffPreviewURL(value){
 if(typeof value!=='string'||!value||value.includes('\\'))return null;
 try{const url=new URL(value,'http://bearing.local/');return url.origin==='http://bearing.local'&&url.pathname.startsWith('/assets/films/')&&/\.(mp4|vtt)$/.test(url.pathname)&&!url.search&&!url.hash?url.pathname:null;}catch{return null;}
}
export function handoffScriptWords(draft){return ['opening','body','closing'].flatMap(phase=>(draft?.[phase]||[]).map(block=>block.text||'')).join(' ').trim().split(/\s+/).filter(Boolean).length;}
export function handoffDraft(selection,fields){
 const refs=[...new Set(['opening','body','closing'].flatMap(phase=>(fields[phase]||[]).flatMap(block=>block.evidence.map(ref=>ref.id))))];
 const previous=selection?.draft?.visuals||[],oldIntent=previous.map(visual=>visual.description||visual.purpose).join('\n');
 return {title:fields.title.trim(),opening:fields.opening,body:fields.body,closing:fields.closing,pronunciations:fields.pronunciations.split('\n').map(x=>x.trim()).filter(Boolean),issues:fields.issues.split('\n').map(x=>x.trim()).filter(Boolean),
  visuals:fields.visualIntent===oldIntent&&previous.length?structuredClone(previous):[{kind:'motion',purpose:'Explain the supported story at its spoken cues.',description:fields.visualIntent.trim(),evidenceIds:refs}]};
}

if(typeof document!=='undefined')boot();

function boot(){
 const $=id=>document.getElementById(id),node=(tag,cls,text)=>{const item=document.createElement(tag);if(cls)item.className=cls;if(text!==undefined)item.textContent=text;return item;};
 let snapshot=null,mode='live',product='brief',filter='today',page=0,selectedId=null,requestNumber=0,controller=null,busy=false,detailKey='',lastViewRefresh=null;
 const drafts=new Map(),cards=new Map();
 const text=(id,value)=>{$(id).textContent=value||'';};
 const date=value=>{if(!value)return 'Time unverified';const parsed=new Date(value);return Number.isFinite(parsed.getTime())?parsed.toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZone:'America/Chicago',timeZoneName:'short'}):'Time unverified';};
 const selected=()=>snapshot?.events?.find(event=>event.id===selectedId);
 const draftKey=()=>`${mode}:${selectedId}`;
 const list=(value)=>Array.isArray(value)?value:[];
 function focusKey(){const element=document.activeElement;return element?.id?{id:element.id}:element?.dataset.eventId?{eventId:element.dataset.eventId}:element?.dataset.action?{action:element.dataset.action}:element?.dataset.focusKey?{detail:element.dataset.focusKey}:null;}
 function restoreFocus(key){if(!key||document.activeElement!==document.body)return;const target=key.id?$(key.id):key.eventId?cards.get(key.eventId):key.action?document.querySelector(`[data-action="${key.action}"]`):[...document.querySelectorAll('[data-focus-key]')].find(element=>element.dataset.focusKey===key.detail);target?.focus({preventScroll:true});}
 function setBusy(value){busy=value;$('refresh').disabled=value;$('input-mode').disabled=value;$('cycle-reset').disabled=value;$('cycle-advance').disabled=value||snapshot?.demo?.canAdvance===false;document.querySelectorAll('[data-action]').forEach(button=>button.disabled=value||!selected());}
 async function request(path,body){
  const ticket=++requestNumber,requestFocus=focusKey();controller?.abort();const requestController=new AbortController();controller=requestController;setBusy(true);$('request-error').hidden=true;
  try{
   const timeout=setTimeout(()=>requestController.abort(),12000);let response;
   try{response=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,cache:'no-store',signal:requestController.signal});}finally{clearTimeout(timeout);}
   if(!response.ok){let message='The reporting workspace could not refresh.';try{const error=await response.json();if(typeof error.error==='string')message=error.error;}catch{}throw new Error(message);}
   const data=await response.json();if(ticket!==requestNumber)return null;
   if(!Array.isArray(data.events)||!data.rankings||data.mode!==mode)throw new Error('The workspace received an incomplete reporting snapshot.');
   snapshot=data;lastViewRefresh=new Date();render();return data;
  }catch(error){if(ticket!==requestNumber)return null;text('request-error',error.name==='AbortError'?'The reporting check took too long. Your last view is retained; try Refresh.':error.message||'The reporting workspace is unavailable.');$('request-error').hidden=false;$('connection-dot').dataset.status='error';if(!snapshot){text('health-message','Reporting unavailable. No candidates have been loaded.');$('candidates').replaceChildren(node('p','empty-state','We could not reach the reporting stream. Refresh to try again.'));}return null;
  }finally{if(ticket===requestNumber){setBusy(false);restoreFocus(requestFocus);}}
 }
 function refresh(){if(!busy)void request(`/api/producer?mode=${mode}`);}
 function render(){
  const focus=focusKey(),scroll=$('candidates').scrollTop;renderHealth();renderCoverage();renderDefinitions();renderList();renderDetail();$('candidates').scrollTop=scroll;restoreFocus(focus);
 }
 function renderHealth(){
  text('strategy-name',snapshot.assignment?'U.S. NATIONAL · CONSEQUENTIAL WORLD':snapshot.strategy?.name||'YOUR EDITORIAL VIEW');
  const health=snapshot.sourceHealth||{},old=health.stale===true;
  $('connection-dot').dataset.status=mode==='demo'?'stale':old||!health.healthy||health.healthy<health.total?'stale':'healthy';
  if(mode==='demo')text('health-message','Representative reporting · isolated from the live editorial record');
  else text('health-message',`${Number.isFinite(health.healthy)?`${health.healthy} of ${health.total||0} feeds available`:'Feed availability unverified'} · ${health.checkedAt?`${old?'Last reporting check':'Reporting checked'} ${date(health.checkedAt)}`:'Reporting check time unavailable'}${old?' · Refresh may be delayed':''}`);
  text('refresh-time',lastViewRefresh?`View refreshed ${lastViewRefresh.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'})} · View checks every 30s`:'');
  $('cycle-banner').hidden=mode!=='demo';
  if(mode==='demo'){const demo=snapshot.demo||{};text('cycle-description',`${demo.label||'Review the next development'} · Step ${Number(demo.step)+1||1} of ${demo.totalSteps||'—'}. Synthetic examples, not current news.`);$('cycle-advance').disabled=busy||demo.canAdvance===false;text('cycle-advance',demo.canAdvance===false?'Cycle complete':'Next development →');}
 }
 function renderCoverage(){
  const desk=snapshot.assignment,panel=$('desk-coverage');panel.hidden=!desk;if(!desk)return;
  const counts=desk.counts||{},health=desk.health||{},coverageScroll=panel.querySelector('.coverage-content').scrollTop,calendarOpen=panel.querySelector('.release-calendar')?.open||false;
  text('coverage-summary',`${counts.today||0} today · ${counts.developing||0} developing · ${counts.watch||0} watching`);
  text('coverage-context',`${desk.date||'Current cycle'} · ${desk.scope||'U.S. national + consequential world'} · ${desk.timezone||'America/Chicago'}. Coverage describes the collected reporting, not the entire news agenda.`);
  const beats=$('coverage-beats');beats.replaceChildren();
  for(const beat of list(desk.coverage)){
   const card=node('div','coverage-beat');card.dataset.gap=String(!!beat.gap);
   card.append(node('strong','',beat.label||beat.id),node('span','coverage-count',`${beat.currentCount||0} current leads · ${beat.reportCount||0} reports`));
   const publishers=list(beat.publishers),primary=list(beat.primarySources);
   card.append(node('p','',publishers.length?publishers.join(' · '):'No publisher reporting collected'));
   if(primary.length)card.append(node('p','coverage-primary',`Connected primary feeds: ${primary.join(' · ')}`));
   if(beat.gap)card.append(node('p','coverage-gap',beat.gap));beats.append(card);
  }
  const healthNode=$('coverage-health');healthNode.replaceChildren();
  healthNode.append(node('span','',`${health.healthySources??'—'} / ${health.sourceCount??'—'} sources available`),node('span','',`Collection checked: ${date(health.lastCollectedAt)}`),node('span','',`Discovery lag: median ${discoveryLag(health.medianDiscoveryMinutes)} · P90 ${discoveryLag(health.p90DiscoveryMinutes)} · ${health.latencySamples||0} samples`));
  healthNode.append(node('p','', 'Discovery lag measures source publication to first collection. It is not a measurement of when an event happened or how quickly another newsroom reported it.'));
  if(list(desk.sourceGaps).length){
   const gaps=node('section','coverage-source-gaps');gaps.append(node('h3','','Sources to strengthen'));
   for(const source of desk.sourceGaps){const row=node('div','release-row'),url=safeSourceURL(source.url),name=node(url?'a':'strong','',source.name||'Source');if(url){name.href=url;name.target='_blank';name.rel='noopener noreferrer';}row.append(name,node('span','',String(source.status||'Not connected').replaceAll('-',' ')));if(source.reason)row.append(node('p','',source.reason));gaps.append(row);}healthNode.append(gaps);
  }
  if(list(desk.watchpoints).length){
   const calendar=node('details','release-calendar'),summary=node('summary','','Scheduled releases');calendar.open=calendarOpen;calendar.append(summary,node('p','', 'A scheduled release is a reporting prompt. Confirm that the report is out before using its findings.'));
   for(const release of desk.watchpoints){const row=node('div','release-row'),url=safeSourceURL(release.sourceUrl),title=node(url?'a':'strong','',release.title);if(url){title.href=url;title.target='_blank';title.rel='noopener noreferrer';}row.append(title,node('span','',`${release.status==='due'?'Due — check source':'Scheduled'} · ${date(release.scheduledAt)} · ${release.sourceName||'Official calendar'}`));if(release.note)row.append(node('p','',release.note));calendar.append(row);}healthNode.append(calendar);
  }
  const limits=$('coverage-limitations');limits.replaceChildren();for(const limit of [...new Set([...list(desk.limitations),...list(health.limitations)])])limits.append(node('li','',limit));panel.querySelector('.coverage-content').scrollTop=coverageScroll;
 }
 function cardBadge(event){if(snapshot.assignment&&event.assignment){const lane=event.assignment.lane;return {text:assignmentLanes[lane]||'Needs review',kind:lane==='today'||lane==='developing'?'update':'watch'};}const freshness=freshnessLabel(event);if(freshness)return {text:freshness,kind:'watch'};if(event.signals?.update)return {text:'Meaningful update',kind:'update'};if(event.localSignal)return {text:'Local signal',kind:'local'};if(event.decision?.action==='watch'||event.signals?.watch)return {text:'Watch',kind:'watch'};return {text:'Candidate',kind:'candidate'};}
 function renderList(){
  const filters=candidateFilters(snapshot),filterKey=JSON.stringify(filters);if($('candidate-filter').dataset.options!==filterKey){$('candidate-filter').replaceChildren(...filters.map(([value,label])=>{const option=node('option','',label);option.value=value;return option;}));$('candidate-filter').dataset.options=filterKey;}if(!filters.some(([value])=>value===filter))filter=filters[0][0];$('candidate-filter').value=filter;
  const batch=candidatePage(snapshot,product,filter,page);page=batch.page;
  document.querySelectorAll('[data-product]').forEach(button=>{button.setAttribute('aria-selected',String(button.dataset.product===product));button.tabIndex=button.dataset.product===product?0:-1;});
  $('candidates').setAttribute('aria-labelledby',`product-${product}`);
  text('ranking-note',snapshot.assignment?'National significance and a today peg lead. Signals need editorial verification.':product==='brief'?'Ranked for immediate audience awareness. A candidate is not an assignment.':'Ranked for explanatory value and reporting potential. A candidate is not an assignment.');
  if(!selectedId||!selected()){selectedId=batch.items[0]?.id||null;detailKey='';}
  const wanted=new Set(batch.items.map(event=>event.id));for(const child of [...$('candidates').children])if(!wanted.has(child.dataset.eventId))child.remove();
  if(!batch.items.length){const empty=filter==='developing'?'No material reporting changes to inspect right now.':filter==='today'?'No national leads have a candidate today peg yet.':filter==='watch'?'No reporting leads are being watched in this view.':filter==='all'?'No candidates meet this view yet. The reporting stream remains available for the next development.':`No stories in ${$('candidate-filter').selectedOptions[0].textContent.toLowerCase()} right now.`;$('candidates').replaceChildren(node('p','empty-state',`${empty} Choose another filter to keep exploring.`));}
  for(const [index,event] of batch.items.entries()){
   let card=cards.get(event.id);if(!card){card=node('button','candidate-card');card.dataset.eventId=event.id;card.addEventListener('click',()=>choose(event.id));cards.set(event.id,card);}
   const key=JSON.stringify([event,product,index,page]);if(card.dataset.renderKey!==key){
    const top=node('span','card-top'),badge=cardBadge(event),badgeNode=node('span','card-badge',badge.text);badgeNode.dataset.kind=badge.kind;
    const clock=snapshot.assignment?assignmentReportClock(event):{label:'',at:event.whyNow?.at};
    top.append(node('span','card-index',String(page*PAGE_SIZE+index+1).padStart(2,'0')),badgeNode,node('span','card-time',`${clock.label?`${clock.label} `:''}${relativeTime(clock.at,snapshot.asOf||snapshot.generatedAt)}`));
    const reason=(event.assignment?.lane==='held'?(nationalScopes.has(event.assignment.scope)?event.assignment.questions?.[0]:event.assignment.scopeReason):null)||event.assignment?.todayPeg?.label||event.fits?.[product]?.reasons?.[0]?.text||event.strategy?.reason||event.whyNow?.text||'';
    const publishers=[...new Set(list(event.evidence).map(source=>source.publisher).filter(Boolean))],sources=node('span','card-sources',publishers.slice(0,2).join(' · ')+(publishers.length>2?` +${publishers.length-2}`:''));
    if(event.decision?.action&&event.decision.action!=='none')sources.append(node('span','card-state',actionNames[event.decision.action]||''));
    card.replaceChildren(top,node('span','card-title',event.title),node('span','card-reason',reason),sources);card.dataset.renderKey=key;
   }
   card.setAttribute('aria-current',String(event.id===selectedId));card.setAttribute('aria-label',`Inspect ${event.title}`);
   const position=$('candidates').children[index];if(position!==card)$('candidates').insertBefore(card,position||null);
  }
  text('candidate-count',batch.total?`${batch.start}–${batch.end} of ${batch.total} opportunities`:'No opportunities in this view');$('previous-page').disabled=page===0;$('next-page').disabled=page>=batch.pages-1;
 }
 function choose(id){drafts.set(draftKey(),$('decision-note').value);selectedId=id;detailKey='';$('detail-scroll').scrollTop=0;text('decision-feedback','Decisions are saved here. Nothing is assigned or published.');renderList();renderDetail();}
 function section(title){const block=node('section','detail-section');block.append(node('h3','',title));return block;}
 function renderDetail(){
  const event=selected();$('detail-empty').hidden=!!event;$('story-detail').hidden=!event;$('decision-panel').hidden=!event;if(!event)return;
  const localBasis=event.localSignal?localSignalSources(snapshot,event.localSignal):null,key=JSON.stringify([event,product,localBasis]);if(detailKey===key)return;detailKey=key;
  const scroll=$('detail-scroll').scrollTop,historyOpen=$('story-detail').querySelector('.history')?.open||false,openedExcerpts=new Set([...$('story-detail').querySelectorAll('details[data-evidence]')].filter(item=>item.open).map(item=>item.dataset.evidence)),article=$('story-detail');article.replaceChildren();
  const meta=node('div','detail-meta'),badge=cardBadge(event),badgeNode=node('span','card-badge',badge.text),heading=node('h2','detail-title',event.title),clock=snapshot.assignment?assignmentReportClock(event):{label:'',at:event.whyNow?.at};heading.tabIndex=-1;heading.dataset.focusKey='detail-heading';badgeNode.dataset.kind=badge.kind;meta.append(badgeNode,node('span','',event.assignment?.beatLabel||event.topic||'Reporting'),node('span','detail-date',`${clock.label?`${clock.label} `:''}${date(clock.at)}`));article.append(meta,heading);
  const excerptSource=list(event.evidence).find(source=>source.excerpt&&source.excerpt===event.summary);
  if(excerptSource){const preview=node('div','story-preview'),excerpt=String(excerptSource.excerpt),short=excerpt.length>260?excerpt.slice(0,260).replace(/\s+\S*$/,'')+'…':excerpt;preview.append(node('p','',short),node('span','',`${excerptSource.publisher} · ${mode==='demo'?'representative excerpt':'available excerpt'}`));article.append(preview);}
  if(snapshot.assignment&&event.assignment){
   const desk=event.assignment,peg=desk.todayPeg||{},source=assignmentPegSource(event),why=node('section','why-now assignment-peg');
   why.append(node('span','section-label',peg.status==='candidate'?'Candidate today peg':peg.status==='needs-verification'?'Today peg needs verification':'Today peg not established'),node('h3','',peg.label||'Verify what is new and why it matters today'),node('p','',peg.reason||'A recent collection is not enough to establish a current development.'));
   if(peg.quote){why.append(node('blockquote','',peg.quote));const url=safeSourceURL(source?.url);const citation=node(url?'a':'span','peg-citation',source?`${source.publisher||'Source'} · ${sourceClockLabel(source).toLowerCase()} ${date(source.publishedAt)}`:'The cited source is unavailable in this snapshot.');if(url){citation.href=url;citation.target='_blank';citation.rel='noopener noreferrer';}why.append(citation);}
   why.append(node('p','supporting-detail',`${desk.scope==='world-impact'?'World impact':desk.scope==='national'?'National scope':desk.scope==='local'?'Local scope — outside this desk':'National relevance not established'} · ${desk.scopeReason||'The scope requires editorial review.'}`));article.append(why);
   if(list(desk.questions).length){const questions=section('Next reporting questions'),ul=node('ul','gap-list');for(const question of desk.questions)ul.append(node('li','',question));questions.append(ul);article.append(questions);}
  }else{const why=node('div','why-now');why.append(node('span','section-label','Why this matters now'),node('p','',readableReportingText(event.whyNow?.text)||'The current reason to cover this story still needs verification.'));article.append(why);}
  const change=section('What changed'),changeRow=node('div','change-note'),changeCopy=node('div','');
  changeRow.append(node('span','change-mark',event.change?.material?'↗':'—'));changeCopy.append(node('strong','',event.change?.material?'Potential material change':({new:'First surfaced in this view',cosmetic:'Headline wording changed', 'source-added':'Additional reporting',unchanged:'No material change detected'})[event.change?.kind]||'Change still needs review'),node('p','',readableReportingText(event.change?.text)||'No supported material change has been identified.'));changeRow.append(changeCopy);change.append(changeRow);
  const revisions=list(event.change?.details);for(const reason of [...new Set(revisions.map(detail=>detail.reason).filter(Boolean))].slice(0,3))change.append(node('p','supporting-detail',reason));
  if(revisions.some(detail=>detail.before||detail.after)){
   const comparison=node('details','revision-comparison'),summary=node('summary','','Compare source revisions');comparison.dataset.evidence='revision-comparison';comparison.open=openedExcerpts.has('revision-comparison');summary.dataset.focusKey='revision-comparison';comparison.append(summary);
   for(const detail of revisions){const pair=node('div','revision-pair');if(detail.before)pair.append(node('span','section-label','Before'),node('blockquote','',detail.before));if(detail.after)pair.append(node('span','section-label','After'),node('blockquote','',detail.after));comparison.append(pair);}change.append(comparison);
  }article.append(change);
  const strategy=section('Why it fits your strategy');strategy.append(node('p','',event.strategy?.reason||'Editorial strategy fit needs review.'));article.append(strategy);
  const fits=section('Where this story could work'),fitGrid=node('div','fit-grid');
  for(const id of ['brief','focus']){const fit=event.fits?.[id]||{},card=node('div',`fit-card${product===id?' is-selected':''}`),top=node('div','fit-top');top.append(node('strong','',productNames[id]),node('span','fit-rating',fit.label||'Needs review'));card.append(top,node('p','fit-purpose',snapshot.strategy?.products?.find(item=>item.id===id)?.purpose||''));for(const reason of list(fit.reasons).slice(0,3))card.append(node('p','',reason.text));if(list(fit.gaps).length)card.append(node('p','fit-needs',`Needs: ${fit.gaps.join(' · ')}`));fitGrid.append(card);}fits.append(fitGrid);article.append(fits);
  if(event.localSignal){
   const local=section(event.localSignal.label||'A possible wider pattern');local.append(node('p','',event.localSignal.reason),node('p','supporting-detail',event.localSignal.caveat||'Converging local reporting is a reporting lead, not proof of a national trend.'));
   const origins=node('ul','local-origins');for(const report of localBasis.reports){
    const origin=node('li',''),url=safeSourceURL(report.url),headline=node(mode==='live'&&url?'a':'span','local-headline',report.title||'Source report'),meta=node('div','local-origin-meta');meta.append(node('strong','',report.market||'Market not recorded'),node('span','',report.publisher||'Publisher not recorded'));origin.append(meta);
    if(mode==='live'&&url){headline.href=url;headline.target='_blank';headline.rel='noopener noreferrer';headline.dataset.focusKey=`local-source:${report.id}`;}origin.append(headline);
    if(mode==='demo')origin.append(node('span','local-fixture','Synthetic source fixture'));
    if(report.eventId!==event.id){const inspect=node('button','local-inspect','Inspect reporting →');inspect.dataset.focusKey=`local-inspect:${report.id}`;inspect.addEventListener('click',()=>{choose(report.eventId);$('story-detail').querySelector('.detail-title')?.focus({preventScroll:true});});origin.append(inspect);}origins.append(origin);
   }local.append(origins);if(localBasis.missingIds.length)local.append(node('p','supporting-detail',`${localBasis.missingIds.length} referenced report${localBasis.missingIds.length===1?' is':'s are'} unavailable in this snapshot. Verify the full basis before relying on this pattern.`));article.append(local);
  }
  const gaps=[...new Set(list(event.gaps))];if(gaps.length){const readiness=section('Before production'),ul=node('ul','gap-list');for(const gap of gaps)ul.append(node('li','',gap));readiness.append(ul);article.append(readiness);}
  const sources=section('Supporting reporting'),sourceList=node('div','source-list');let links=0;
  for(const evidence of list(event.evidence)){
   const url=safeSourceURL(evidence.url);if(!url&&mode!=='demo')continue;const entry=node('div','source-entry'),link=node(mode==='demo'?'div':'a','source-link'),name=node('span','source-name',evidence.publisher||'Source'),identity=String(evidence.id||url||links);
   if(mode!=='demo'){link.href=url;link.target='_blank';link.rel='noopener noreferrer';link.dataset.focusKey=`source:${identity}`;}
   name.append(node('time','',`${snapshot.assignment?`${sourceClockLabel(evidence)} `:''}${date(evidence.publishedAt)}`));if(mode!=='demo')name.append(node('span','external','↗'));link.append(name,node('span','source-headline',evidence.title||'Read the original report'));
   if(snapshot.assignment&&evidence.firstSeenAt)link.append(node('span','supporting-detail',`First collected ${date(evidence.firstSeenAt)}`));
   if(mode==='demo')link.append(node('span','supporting-detail','Synthetic source fixture · not a live article'));else if(evidence.level==='headline')link.append(node('span','supporting-detail','Headline evidence · full reporting still needs review'));entry.append(link);
   if(evidence.excerpt){const excerpt=node('details','source-excerpt'),summary=node('summary','',mode==='demo'?'Inspect representative reporting':'Read the available excerpt');excerpt.dataset.evidence=identity;excerpt.open=openedExcerpts.has(identity);summary.dataset.focusKey=`excerpt:${identity}`;excerpt.append(summary,node('blockquote','',evidence.excerpt));entry.append(excerpt);}sourceList.append(entry);links++;
  }
  if(!links)sourceList.append(node('p','',mode==='demo'?'This representative example is synthetic. No article is presented as real reporting.':'No verified source link is available. This story needs source review.'));sources.append(sourceList);article.append(sources);
  const history=node('details','history');history.open=historyOpen;const decisions=list(event.decision?.history),changes=list(event.history),historySummary=node('summary','',`Editorial record · ${decisions.length} decision${decisions.length===1?'':'s'}${changes.length?` · ${changes.length} development${changes.length===1?'':'s'}`:''}`);historySummary.dataset.focusKey='editorial-history';history.append(historySummary);const items=node('ol','history-list');for(const entry of [...decisions].reverse()){const li=node('li','');li.append(node('strong','',actionNames[entry.action]||'Editorial decision'),node('time','',date(entry.at)));if(entry.note)li.append(node('p','',entry.note));items.append(li);}for(const entry of [...changes].reverse().slice(0,6)){const li=node('li','');li.append(node('strong','',entry.material?'Potential material change':'Reporting record'),node('time','',date(entry.at)),node('p','',entry.text||entry.kind||''));items.append(li);}if(!items.children.length)items.append(node('li','','No editorial decisions yet.'));history.append(items);article.append(history);
  const draft=drafts.get(draftKey())||'';if($('decision-note').value!==draft)$('decision-note').value=draft;text('decision-current',actionNames[event.decision?.action]||'Not yet reviewed');document.querySelectorAll('[data-action]').forEach(button=>{button.setAttribute('aria-pressed',String(button.dataset.action===event.decision?.action));button.disabled=busy;});$('detail-scroll').scrollTop=scroll;
 }
 function renderDefinitions(){
  const panel=$('strategy-content'),key=JSON.stringify([snapshot.strategy,snapshot.limitations]);if(panel.dataset.renderKey===key)return;panel.dataset.renderKey=key;panel.replaceChildren();const strategy=node('section','definition');strategy.append(node('h3','',snapshot.strategy?.name||'Configured strategy'),node('p','',snapshot.strategy?.summary||'Strategy details unavailable.'));panel.append(strategy);
  for(const product of list(snapshot.strategy?.products)){const block=node('section','definition');block.append(node('h3','',product.name),node('p','',product.purpose||''));if(product.format)block.append(node('p','',Array.isArray(product.format)?product.format.join(' · '):product.format));if(product.freshnessHours)block.append(node('p','supporting-detail',`Freshness guidance: ${product.freshnessHours} hours. A new retrieval alone does not make an old story current.`));panel.append(block);}
  if(list(snapshot.limitations).length){const block=node('section','definition');block.append(node('h3','','Reporting boundaries'));const ul=node('ul','');for(const limit of snapshot.limitations)ul.append(node('li','',limit));block.append(ul);panel.append(block);}
 }
 $('refresh').addEventListener('click',refresh);
 $('input-mode').addEventListener('change',()=>{drafts.set(draftKey(),$('decision-note').value);mode=$('input-mode').value;filter=mode==='live'?'today':'all';snapshot=null;selectedId=null;page=0;detailKey='';text('health-message',mode==='demo'?'Loading an isolated representative cycle…':'Connecting to live reporting…');$('cycle-banner').hidden=mode!=='demo';$('desk-coverage').hidden=true;$('story-detail').hidden=true;$('decision-panel').hidden=true;$('detail-empty').hidden=false;$('candidates').replaceChildren(node('p','empty-state','Loading this reporting view…'));void request(`/api/producer?mode=${mode}`);});
 $('candidate-filter').addEventListener('change',()=>{drafts.set(draftKey(),$('decision-note').value);filter=$('candidate-filter').value;selectedId=null;detailKey='';page=0;if(snapshot){renderList();renderDetail();$('candidates').scrollTop=0;$('detail-scroll').scrollTop=0;}});
 for(const button of document.querySelectorAll('[data-product]')){button.addEventListener('click',()=>{product=button.dataset.product;page=0;if(snapshot){renderList();renderDetail();$('candidates').scrollTop=0;}});button.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const id=event.key==='Home'?'brief':event.key==='End'?'focus':product==='brief'?'focus':'brief';$(`product-${id}`).click();$(`product-${id}`).focus();});}
 $('previous-page').addEventListener('click',()=>{page--;renderList();$('candidates').scrollTop=0;});$('next-page').addEventListener('click',()=>{page++;renderList();$('candidates').scrollTop=0;});
 $('decision-note').addEventListener('input',()=>drafts.set(draftKey(),$('decision-note').value));
 for(const button of document.querySelectorAll('[data-action]'))button.addEventListener('click',async()=>{if(busy||!selected())return;const event=selected(),key=draftKey(),note=$('decision-note').value,action=button.dataset.action;text('decision-feedback','Saving the editorial decision…');const data=await request('/api/producer/decision',{eventId:event.id,action,note,mode});if(data){if(drafts.get(key)===note)drafts.delete(key);if(selectedId===event.id)$('decision-note').value=drafts.get(key)||'';text('decision-feedback',`${actionNames[action]} · saved to the editorial record. You can change this decision at any time.`);}else text('decision-feedback','The decision was not saved. Your note is retained; try again.');});
 $('cycle-advance').addEventListener('click',()=>{if(!busy&&mode==='demo')void request('/api/producer/demo',{action:'advance'});});$('cycle-reset').addEventListener('click',()=>{if(!busy&&mode==='demo'){drafts.forEach((_,key)=>{if(key.startsWith('demo:'))drafts.delete(key);});void request('/api/producer/demo',{action:'reset'});}});
 $('strategy-open').addEventListener('click',()=>$('strategy-dialog').showModal());$('strategy-close').addEventListener('click',()=>$('strategy-dialog').close());$('strategy-dialog').addEventListener('click',event=>{if(event.target===$('strategy-dialog')){const rect=$('strategy-dialog').getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)$('strategy-dialog').close();}});
 bootHandoff(()=>({event:selected(),mode,product}));
 void request('/api/producer?mode=live');setInterval(()=>{if(!document.hidden)refresh();},30000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
}

function bootHandoff(current){
 const $=id=>document.getElementById(id),dialog=$('handoff-dialog');if(!dialog)return;
 const node=(tag,cls,text)=>{const element=document.createElement(tag);if(cls)element.className=cls;if(text!==undefined)element.textContent=text;return element;};
 const labels={selected:'Story selected',draft:'Script awaiting review',approved:'Script and plan approved',held:'Held for editorial work',rejected:'Rejected', 'needs-reassessment':'Reporting needs reassessment',producing:'Producing preview',complete:'Preview complete'};
 const memory=new Map(),selectionNotes=new Map(),reviewNotes=new Map();let target=null,selection=null,loadedRevision=null,dirty=false,busy=false,ticket=0,checked=0,conflict=false;
 const key=()=>`${target?.mode}:${target?.event?.id}`;
 const message=(id,text)=>{$(id).textContent=text||'';};
 const date=value=>{const parsed=new Date(value);return value&&Number.isFinite(parsed.getTime())?parsed.toLocaleString():'Time not recorded';};
 const evidence=()=>selection?.evidence||[];
 function fields(){
  const data={title:$('handoff-script-title').value,pronunciations:$('handoff-pronunciations').value,visualIntent:$('handoff-visual-intent').value,issues:$('handoff-issues').value};
  for(const phase of ['opening','body','closing'])data[phase]=[...$('handoff-passages').querySelectorAll(`[data-phase="${phase}"]`)].map(block=>({text:block.querySelector('[data-copy]').value.trim(),evidence:[...block.querySelectorAll('[data-citation]')].map(ref=>({id:ref.querySelector('select').value,quote:ref.querySelector('textarea').value.trim()}))}));
  return data;
 }
 function remember(){if(!target)return;reviewNotes.set(key(),$('handoff-review-note').value);if(selection&&dirty)memory.set(key(),{fields:fields(),revision:loadedRevision});if(!selection)selectionNotes.set(key(),{product:$('handoff-treatment').value,why:$('handoff-why').value,note:$('handoff-note').value});}
 function sourceSelect(value){const select=node('select');select.setAttribute('aria-label','Source supporting this passage');for(const source of evidence()){const option=node('option','',`${source.publisher} · ${source.headline||source.title||source.id}`);option.value=source.id;select.append(option);}if(value&&!evidence().some(source=>source.id===value)){const option=node('option','','Earlier source · reassessment needed');option.value=value;select.append(option);}if(value)select.value=value;return select;}
 function citation(parent,ref={}){const row=node('div','handoff-citation');row.dataset.citation='';const select=sourceSelect(ref.id),quote=node('textarea');quote.rows=2;quote.required=true;quote.placeholder='Paste the exact supporting excerpt';quote.value=ref.quote||'';quote.setAttribute('aria-label','Exact supporting source excerpt');const remove=node('button','quiet-button','Remove citation');remove.type='button';remove.addEventListener('click',()=>{if(parent.querySelectorAll('[data-citation]').length>1){row.remove();edited();}});row.append(select,quote,remove);parent.append(row);}
 function fillDraft(saved=null){
  const draft=selection?.draft,cache=saved||null;
  $('handoff-script-title').value=cache?.title??draft?.title??target.event.title;
  $('handoff-pronunciations').value=cache?.pronunciations??(draft?.pronunciations||[]).map(x=>typeof x==='string'?x:[x.word||x.term,x.pronunciation||x.sayAs].filter(Boolean).join(' — ')).join('\n');
  $('handoff-visual-intent').value=cache?.visualIntent??(draft?.visuals||[]).map(x=>x.description||x.purpose).join('\n');
  $('handoff-issues').value=cache?.issues??(draft?.issues||[]).join('\n');
  const passages=$('handoff-passages');passages.replaceChildren();
  for(const phase of ['opening','body','closing']){
   const section=node('fieldset','handoff-passage-group');section.append(node('legend','',({opening:'Opening',body:'Story',closing:'Close'})[phase]));
   for(const [index,block] of (cache?.[phase]||draft?.[phase]||[{text:'',evidence:[]}]).entries()){
    const passage=node('div','handoff-passage');passage.dataset.phase=phase;const copy=node('textarea');copy.rows=phase==='body'?3:2;copy.required=true;copy.dataset.copy='';copy.value=block.text;copy.setAttribute('aria-label',`${phase} passage ${index+1}`);passage.append(copy);
    const support=node('details','handoff-citations');support.open=!block.evidence?.length;support.append(node('summary','','Source support · exact excerpts'));
    for(const ref of block.evidence?.length?block.evidence:[{}])citation(support,ref);
    const add=node('button','quiet-button','Add supporting source');add.type='button';add.addEventListener('click',()=>{citation(support);edited();});support.append(add);passage.append(support);section.append(passage);
   }passages.append(section);
  }
  $('handoff-reviewed').checked=false;
 }
 function edited(){dirty=true;remember();updateActions();}
 function updateActions(){
  const allowed=handoffActions(selection,{dirty:dirty||conflict,busy,actor:$('handoff-actor').value,reviewed:$('handoff-reviewed').checked});
  $('handoff-select').disabled=busy;$('handoff-check').disabled=busy;$('handoff-save').disabled=!allowed.save;
  for(const action of ['approve','hold','reject','reassess','produce'])$('handoff-'+action).disabled=action==='hold'||action==='reject'?!allowed.review:!allowed[action];
  $('handoff-load').disabled=busy||!selection;
  if(selection){const count=handoffScriptWords(fields());message('handoff-word-count',`${count} words`);message('handoff-unsaved',conflict?'A newer saved revision exists. Your edits are retained. Load the saved draft to reconcile before continuing.':dirty?'Unsaved edits · save before making a review decision.':'Saved copy · source checks and the prepared plan still govern approval.');}
 }
 function renderEvidence(){
  const panel=$('handoff-evidence');panel.replaceChildren();
  if(evidence().some(source=>source.origin==='reviewed-primary'))panel.append(node('p','supporting-detail','Primary sources must be reread before production; reviews expire after one hour. A local reporting check does not verify an unseen change on the source website.'));
  for(const source of evidence()){
   const block=node('div','handoff-source'),url=safeSourceURL(source.url),link=node(url?'a':'strong','',source.publisher||source.id);if(url){link.href=url;link.target='_blank';link.rel='noopener noreferrer';}block.append(link,node('p','',source.headline||source.title||''),node('span','supporting-detail',`${source.origin==='reviewed-primary'?'Reviewed primary source':'Carried reporting'} · Published ${date(source.publishedTime)}${source.checkedAt?` · Checked ${date(source.checkedAt)}`:''}`),node('blockquote','',source.excerpt||'Headline only. Full supporting evidence is still needed.'));if(source.reviewNote)block.append(node('p','supporting-detail',source.reviewNote));panel.append(block);
  }
  const view=current(),latest=view.mode===target.mode&&view.event?.id===target.event.id?view.event:target.event;
  if(selection?.reassessment?.required){const changed=(latest?.evidence||[]).filter(source=>{const prior=evidence().find(item=>item.id===source.id);return prior&&(prior.excerpt!==source.excerpt||prior.headline!==source.title);});
   if(changed.length){const compare=node('section','handoff-source');compare.append(node('h3','','Latest reporting for reassessment'),node('p','supporting-detail','Compare this current desk excerpt with the carried evidence above. It has not yet replaced the selected evidence.'));for(const source of changed)compare.append(node('p','',`${source.publisher} · ${source.title}`),node('blockquote','',source.excerpt||'Only headline evidence is available.'));panel.append(compare);}
  }
 }
 function renderPlan(){
  const panel=$('handoff-plan');panel.replaceChildren();const packet=selection?.prepared?.packet;
  if(!packet){panel.append(node('p','','Visual plan needed. The producer must prepare a script-matched picture, sound and rights plan before approval.'));return;}
  const plan=packet.plan||{},review=plan.review||packet.review||{},details=node('dl','handoff-plan-details');
  for(const [name,value] of [['Treatment',plan.visualTreatment],['Narration',plan.speech?.provider||plan.narrationProvider],['Music',plan.soundTreatment],['Duration ceiling',plan.maxDuration?`${plan.maxDuration} seconds`:null],['Rights / disclosure',packet.story?.visualDisclosure],['Accuracy review',packet.story?.reviewMethod]])if(value){details.append(node('dt','',name),node('dd','',String(value)));}
  panel.append(details);
  if(packet.visuals?.description)panel.append(node('p','',packet.visuals.description));
  const beats=plan.beats||plan.visuals||[];if(Array.isArray(beats)&&beats.length){const ul=node('ul','gap-list');for(const beat of beats){if(typeof beat==='string')ul.append(node('li','',beat));else ul.append(node('li','',[beat.cue?`At “${beat.cue}”`:null,beat.layout||beat.kind,beat.title||beat.purpose||beat.description].filter(Boolean).join(' · ')));}panel.append(ul);}
  const reviewItems=Object.entries(review).filter(([,v])=>typeof v==='string'||typeof v==='boolean');if(reviewItems.length)for(const [k,v] of reviewItems)panel.append(node('p','supporting-detail',`${k.replace(/([A-Z])/g,' $1')}: ${v===true?'reviewed':v===false?'not reviewed':v}`));
  if(review.rights&&typeof review.rights==='object')for(const [name,basis] of Object.entries(review.rights)){
   const row=node('p','supporting-detail',`${name.replace(/([A-Z])/g,' $1')}: `),url=typeof basis==='string'?safeSourceURL(basis):null;
   if(url){const link=node('a','','Source rights');link.href=url;link.target='_blank';link.rel='noopener noreferrer';row.append(link);}else row.append(document.createTextNode(typeof basis==='boolean'?(basis?'yes':'no'):typeof basis==='string'?basis:'See the prepared asset review'));panel.append(row);
  }
  const cues=[...(plan.openingReveals||[]),...(Array.isArray(beats)?beats.flatMap(beat=>[beat,...(beat.reveals||[])]):[]),...(plan.closingReveals||[])].filter(beat=>beat.cue);
  if(cues.length){const detail=node('details','handoff-cue-details');detail.append(node('summary','','Narration-linked picture cues'));const list=node('ul','gap-list');for(const cue of cues)list.append(node('li','',`“${cue.cue}” · ${cue.label||cue.text||cue.role||'picture change'}`));detail.append(list);panel.append(detail);}
  const media=plan.media||[];if(Array.isArray(media))for(const item of media)panel.append(node('p','supporting-detail',[item.kind,item.courtesy||item.credit,item.licenseName||item.license,item.reviewNote].filter(x=>typeof x==='string').join(' · ')));
  panel.append(node('p','supporting-detail','This prepared plan is bound to the saved script. Editing the script requires a matching new plan.'));
 }
 function renderProduction(){
  const production=selection?.production,items=$('handoff-artifacts');items.replaceChildren();
  message('handoff-production-note',production?.state==='running'||selection?.state==='producing'?'Producing the approved preview. You can close this review while the local worker finishes.':production?.error?`Production stopped: ${production.error}`:production?.result?'Finished preview. Inspect sound, picture and timing before any separate publication decision.':'Production starts only after explicit editorial approval. It creates a preview, without changing the viewer playlist.');
  for(const [name,voice] of Object.entries(production?.result?.voices||{})){const url=handoffPreviewURL(voice.video);if(!url)continue;const link=node('a','decision-button',`${name==='warm'?'Warm':'Measured'} · ${Number.isFinite(voice.duration)?voice.duration.toFixed(1)+' seconds':'complete film'} ↗`);link.href=url;link.target='_blank';link.rel='noopener noreferrer';items.append(link);}
  const provenance=node('p','supporting-detail');if(selection?.id)provenance.textContent=`Selection ${selection.id} · revision ${selection.revision}${production?.completedAt?` · Completed ${date(production.completedAt)}`:''}`;items.append(provenance);
 }
 function renderHistory(){const list=$('handoff-history');list.replaceChildren();for(const entry of [...(selection?.history||[])].reverse()){const li=node('li','');li.append(node('strong','',entry.action||entry.decision||entry.state||'Editorial update'),node('time','',date(entry.at||entry.createdAt)));const copy=[entry.actor?`By ${entry.actor}`:'',entry.note||entry.reason||entry.detail||'',entry.revision?`Revision ${entry.revision}`:''].filter(x=>typeof x==='string'&&x);if(copy.length)li.append(node('p','',copy.join(' · ')));list.append(li);}}
 function renderRecord({force=false}={}){
  $('handoff-selection').hidden=!!selection;$('handoff-work').hidden=!selection;if(!selection)return;
  const cached=memory.get(key());if(force){memory.delete(key());dirty=false;conflict=false;loadedRevision=selection.revision;fillDraft();}
  else if(dirty||cached){if(!dirty&&cached){loadedRevision=cached.revision;fillDraft(cached.fields);dirty=true;}conflict=loadedRevision!==selection.revision;}
  else if(loadedRevision!==selection.revision){loadedRevision=selection.revision;fillDraft();}
  message('handoff-state',labels[selection.state]||selection.state);message('handoff-revision',`Revision ${selection.revision}`);message('handoff-context',`${selection.product?.name||productNames[selection.productId]||selection.productId} · ${selection.whyNow||''}`);
  const blocked=selection.reassessment?.required||selection.state==='needs-reassessment';$('handoff-blocker').hidden=!blocked;message('handoff-blocker',selection.reassessment?.reason||'Reporting changed. Review the carried evidence, explain the reassessment and revise before production.');
  renderEvidence();renderPlan();renderProduction();renderHistory();updateActions();
 }
 async function request(action=null,payload={}){
  if(!target||busy)return;const context=target,requestKey=key(),serial=++ticket;busy=true;updateActions();$('handoff-error').hidden=true;
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),20000);
  try{
   const url='/api/producer/handoff'+(action?'':`?eventId=${encodeURIComponent(context.event.id)}&mode=${context.mode}`),body=action?{action,eventId:context.event.id,mode:context.mode,...payload}:null;
   const response=await fetch(url,{method:action?'POST':'GET',headers:action?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,cache:'no-store',signal:controller.signal});let data;try{data=await response.json();}catch{throw new Error('Story preparation is unavailable. Your edits are retained; check the saved state shortly.');}
   if(!response.ok){if(response.status===409)conflict=true;throw new Error(data.error||'Story preparation could not be saved.');}
   if(serial!==ticket||requestKey!==key())return;if(!Object.hasOwn(data,'selection'))throw new Error('The story response is incomplete. Your edits are retained.');
   selection=data.selection;checked=Date.now();renderRecord({force:action==='save'||action==='select'||action==='reassess'});message('handoff-feedback',action==='select'?'Source evidence and editorial context carried forward.':action==='save'?'Script revision saved.':action==='review'?'Editorial decision recorded.':action==='produce'?'Approved preview requested.':action==='reassess'?'Reassessment recorded. Review the current evidence and script.':selection?`${labels[selection.state]||selection.state} · ${context.mode==='demo'?'representative cycle':'live reporting'}`:'Choose the treatment and a concrete reason to cover this story now.');
  }catch(error){if(serial===ticket&&requestKey===key()){remember();message('handoff-error',error.name==='AbortError'?'The request took too long. Your edits remain here; the saved state will be checked again.':error.message);$('handoff-error').hidden=false;}}
  finally{clearTimeout(timeout);if(serial===ticket){busy=false;updateActions();}}
 }
 $('handoff-open').addEventListener('click',()=>{const next=current();if(!next.event)return;remember();target=next;selection=null;loadedRevision=null;dirty=false;conflict=false;busy=false;ticket++;$('handoff-work').hidden=true;$('handoff-selection').hidden=true;$('handoff-error').hidden=true;message('handoff-story',next.event.title);message('handoff-feedback','Loading the carried reporting and editorial record…');const notes=selectionNotes.get(key());$('handoff-treatment').value=notes?.product||next.product;$('handoff-why').value=notes?.why||'';$('handoff-note').value=notes?.note||'';$('handoff-review-note').value=reviewNotes.get(key())||'';$('handoff-reviewed').checked=false;dialog.showModal();void request();});
 $('handoff-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('close',remember);
 $('handoff-check').addEventListener('click',()=>void request());
 $('handoff-selection').addEventListener('submit',event=>{event.preventDefault();void request('select',{productId:$('handoff-treatment').value,whyNow:$('handoff-why').value.trim(),note:$('handoff-note').value.trim()});});
 $('handoff-script').addEventListener('input',edited);$('handoff-script').addEventListener('change',edited);
 $('handoff-script').addEventListener('submit',event=>{event.preventDefault();if(!selection)return;void request('save',{expectedRevision:loadedRevision,draft:handoffDraft(selection,fields())});});
 $('handoff-load').addEventListener('click',()=>{if(selection){renderRecord({force:true});message('handoff-feedback','Loaded the saved draft. Local unsaved edits were replaced.');}});
 for(const id of ['handoff-actor','handoff-reviewed'])$(id).addEventListener('input',updateActions);
 for(const decision of ['approve','hold','reject'])$('handoff-'+decision).addEventListener('click',()=>{if(selection)void request('review',{expectedRevision:selection.revision,decision,actor:$('handoff-actor').value.trim(),note:$('handoff-review-note').value.trim()});});
 $('handoff-reassess').addEventListener('click',()=>{const reason=$('handoff-review-note').value.trim();if(!reason){message('handoff-error','Explain the editorial reassessment in the decision note.');$('handoff-error').hidden=false;$('handoff-review-note').focus();return;}void request('reassess',{expectedRevision:selection.revision,reason});});
 $('handoff-produce').addEventListener('click',()=>{if(selection)void request('produce',{expectedRevision:selection.revision});});
 setInterval(()=>{if(dialog.open&&!document.hidden&&!busy&&(selection?.state==='producing'||Date.now()-checked>30000))void request();},5000);
}
