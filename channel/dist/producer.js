const PAGE_SIZE=8;
const productNames={brief:'The Brief',focus:'In Focus'};
const actionNames={none:'Not yet reviewed',shortlist:'Shortlisted',watch:'Watching',dismiss:'Dismissed',reset:'Returned to candidates'};

export function safeSourceURL(value){
 try{const url=new URL(value);return ['http:','https:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null;}catch{return null;}
}
export function rankedCandidates(snapshot,product='brief',filter='all'){
 const events=new Map((snapshot?.events||[]).map(event=>[event.id,event]));
 return (snapshot?.rankings?.[product]||[]).map(id=>events.get(id)).filter(Boolean).filter(event=>{
  const action=event.decision?.action||'none';
  if(filter==='dismissed')return action==='dismiss';
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

if(typeof document!=='undefined')boot();

function boot(){
 const $=id=>document.getElementById(id),node=(tag,cls,text)=>{const item=document.createElement(tag);if(cls)item.className=cls;if(text!==undefined)item.textContent=text;return item;};
 let snapshot=null,mode='live',product='brief',filter='all',page=0,selectedId=null,requestNumber=0,controller=null,busy=false,detailKey='',lastViewRefresh=null;
 const drafts=new Map(),cards=new Map();
 const text=(id,value)=>{$(id).textContent=value||'';};
 const date=value=>{if(!value)return 'Time unverified';const parsed=new Date(value);return Number.isFinite(parsed.getTime())?parsed.toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):'Time unverified';};
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
  const focus=focusKey(),scroll=$('candidates').scrollTop;renderHealth();renderDefinitions();renderList();renderDetail();$('candidates').scrollTop=scroll;restoreFocus(focus);
 }
 function renderHealth(){
  text('strategy-name',snapshot.strategy?.name||'YOUR EDITORIAL VIEW');
  const health=snapshot.sourceHealth||{},old=health.stale===true;
  $('connection-dot').dataset.status=mode==='demo'?'stale':old||!health.healthy||health.healthy<health.total?'stale':'healthy';
  if(mode==='demo')text('health-message','Representative reporting · isolated from the live editorial record');
  else text('health-message',`${Number.isFinite(health.healthy)?`${health.healthy} of ${health.total||0} feeds available`:'Feed availability unverified'} · ${health.checkedAt?`${old?'Last reporting check':'Reporting checked'} ${date(health.checkedAt)}`:'Reporting check time unavailable'}${old?' · Refresh may be delayed':''}`);
  text('refresh-time',lastViewRefresh?`View refreshed ${lastViewRefresh.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'})} · Checks every 30s`:'');
  $('cycle-banner').hidden=mode!=='demo';
  if(mode==='demo'){const demo=snapshot.demo||{};text('cycle-description',`${demo.label||'Review the next development'} · Step ${Number(demo.step)+1||1} of ${demo.totalSteps||'—'}. Synthetic examples, not current news.`);$('cycle-advance').disabled=busy||demo.canAdvance===false;text('cycle-advance',demo.canAdvance===false?'Cycle complete':'Next development →');}
 }
 function cardBadge(event){const freshness=freshnessLabel(event);if(freshness)return {text:freshness,kind:'watch'};if(event.signals?.update)return {text:'Meaningful update',kind:'update'};if(event.localSignal)return {text:'Local signal',kind:'local'};if(event.decision?.action==='watch'||event.signals?.watch)return {text:'Watch',kind:'watch'};return {text:'Candidate',kind:'candidate'};}
 function renderList(){
  const batch=candidatePage(snapshot,product,filter,page);page=batch.page;
  document.querySelectorAll('[data-product]').forEach(button=>{button.setAttribute('aria-selected',String(button.dataset.product===product));button.tabIndex=button.dataset.product===product?0:-1;});
  $('candidates').setAttribute('aria-labelledby',`product-${product}`);
  text('ranking-note',product==='brief'?'Ranked for immediate audience awareness. A candidate is not an assignment.':'Ranked for explanatory value and reporting potential. A candidate is not an assignment.');
  if(!selectedId||!selected()){selectedId=batch.items[0]?.id||snapshot.events[0]?.id||null;detailKey='';}
  const wanted=new Set(batch.items.map(event=>event.id));for(const child of [...$('candidates').children])if(!wanted.has(child.dataset.eventId))child.remove();
  if(!batch.items.length){$('candidates').replaceChildren(node('p','empty-state',filter==='all'?'No candidates meet this view yet. The reporting stream remains available for the next development.':`No ${$('candidate-filter').selectedOptions[0].textContent.toLowerCase()} in this product view. Choose another filter to keep exploring.`));}
  for(const [index,event] of batch.items.entries()){
   let card=cards.get(event.id);if(!card){card=node('button','candidate-card');card.dataset.eventId=event.id;card.addEventListener('click',()=>choose(event.id));cards.set(event.id,card);}
   const key=JSON.stringify([event,product,index,page]);if(card.dataset.renderKey!==key){
    const top=node('span','card-top'),badge=cardBadge(event),badgeNode=node('span','card-badge',badge.text);badgeNode.dataset.kind=badge.kind;
    top.append(node('span','card-index',String(page*PAGE_SIZE+index+1).padStart(2,'0')),badgeNode,node('span','card-time',relativeTime(event.whyNow?.at,snapshot.asOf||snapshot.generatedAt)));
    const reason=event.fits?.[product]?.reasons?.[0]?.text||event.strategy?.reason||event.whyNow?.text||'';
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
  const meta=node('div','detail-meta'),badge=cardBadge(event),badgeNode=node('span','card-badge',badge.text),heading=node('h2','detail-title',event.title);heading.tabIndex=-1;heading.dataset.focusKey='detail-heading';badgeNode.dataset.kind=badge.kind;meta.append(badgeNode,node('span','',event.topic||'Reporting'),node('span','detail-date',date(event.whyNow?.at)));article.append(meta,heading);
  const excerptSource=list(event.evidence).find(source=>source.excerpt&&source.excerpt===event.summary);
  if(excerptSource){const preview=node('div','story-preview'),excerpt=String(excerptSource.excerpt),short=excerpt.length>260?excerpt.slice(0,260).replace(/\s+\S*$/,'')+'…':excerpt;preview.append(node('p','',short),node('span','',`${excerptSource.publisher} · ${mode==='demo'?'representative excerpt':'available excerpt'}`));article.append(preview);}
  const why=node('div','why-now');why.append(node('span','section-label','Why this matters now'),node('p','',readableReportingText(event.whyNow?.text)||'The current reason to cover this story still needs verification.'));article.append(why);
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
   name.append(node('time','',date(evidence.publishedAt)));if(mode!=='demo')name.append(node('span','external','↗'));link.append(name,node('span','source-headline',evidence.title||'Read the original report'));
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
 $('input-mode').addEventListener('change',()=>{drafts.set(draftKey(),$('decision-note').value);mode=$('input-mode').value;snapshot=null;selectedId=null;page=0;detailKey='';text('health-message',mode==='demo'?'Loading an isolated representative cycle…':'Connecting to live reporting…');$('cycle-banner').hidden=mode!=='demo';$('story-detail').hidden=true;$('decision-panel').hidden=true;$('detail-empty').hidden=false;$('candidates').replaceChildren(node('p','empty-state','Loading this reporting view…'));void request(`/api/producer?mode=${mode}`);});
 $('candidate-filter').addEventListener('change',()=>{filter=$('candidate-filter').value;page=0;if(snapshot){renderList();renderDetail();$('candidates').scrollTop=0;}});
 for(const button of document.querySelectorAll('[data-product]')){button.addEventListener('click',()=>{product=button.dataset.product;page=0;if(snapshot){renderList();renderDetail();$('candidates').scrollTop=0;}});button.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const id=event.key==='Home'?'brief':event.key==='End'?'focus':product==='brief'?'focus':'brief';$(`product-${id}`).click();$(`product-${id}`).focus();});}
 $('previous-page').addEventListener('click',()=>{page--;renderList();$('candidates').scrollTop=0;});$('next-page').addEventListener('click',()=>{page++;renderList();$('candidates').scrollTop=0;});
 $('decision-note').addEventListener('input',()=>drafts.set(draftKey(),$('decision-note').value));
 for(const button of document.querySelectorAll('[data-action]'))button.addEventListener('click',async()=>{if(busy||!selected())return;const event=selected(),key=draftKey(),note=$('decision-note').value,action=button.dataset.action;text('decision-feedback','Saving the editorial decision…');const data=await request('/api/producer/decision',{eventId:event.id,action,note,mode});if(data){if(drafts.get(key)===note)drafts.delete(key);if(selectedId===event.id)$('decision-note').value=drafts.get(key)||'';text('decision-feedback',`${actionNames[action]} · saved to the editorial record. You can change this decision at any time.`);}else text('decision-feedback','The decision was not saved. Your note is retained; try again.');});
 $('cycle-advance').addEventListener('click',()=>{if(!busy&&mode==='demo')void request('/api/producer/demo',{action:'advance'});});$('cycle-reset').addEventListener('click',()=>{if(!busy&&mode==='demo'){drafts.forEach((_,key)=>{if(key.startsWith('demo:'))drafts.delete(key);});void request('/api/producer/demo',{action:'reset'});}});
 $('strategy-open').addEventListener('click',()=>$('strategy-dialog').showModal());$('strategy-close').addEventListener('click',()=>$('strategy-dialog').close());$('strategy-dialog').addEventListener('click',event=>{if(event.target===$('strategy-dialog')){const rect=$('strategy-dialog').getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)$('strategy-dialog').close();}});
 void request('/api/producer?mode=live');setInterval(()=>{if(!document.hidden)refresh();},30000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
}
