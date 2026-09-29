const desk=document.querySelector('.view-desk');
const tabs=[...document.querySelectorAll('[data-desk-tab]')];
function activate(tab){
 desk.dataset.desk=tab.dataset.deskTab;
 for(const button of tabs){button.setAttribute('aria-selected',String(button===tab));button.tabIndex=button===tab?0:-1;}
 if(tab.dataset.deskTab!=='cameras')document.querySelectorAll('.camera-stop:not([hidden])').forEach(button=>button.click());
}
for(const [index,tab] of tabs.entries()){
 tab.onclick=()=>activate(tab);
 tab.onkeydown=event=>{let next;if(event.key==='ArrowRight')next=(index+1)%tabs.length;else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;event.preventDefault();activate(tabs[next]);tabs[next].focus();};
}
const queue=document.getElementById('rotation');
const previous=document.getElementById('queue-prev'),next=document.getElementById('queue-next');
function queueState(){previous.disabled=queue.scrollLeft<4;next.disabled=queue.scrollLeft+queue.clientWidth>=queue.scrollWidth-5;}
function move(direction){queue.scrollBy({left:direction*queue.clientWidth,behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});}
previous.onclick=()=>move(-1);next.onclick=()=>move(1);queue.addEventListener('scroll',queueState,{passive:true});
new ResizeObserver(queueState).observe(queue);new MutationObserver(()=>{queueState();document.getElementById('story-title').title=document.getElementById('story-title').textContent;}).observe(queue,{childList:true});
queueState();
