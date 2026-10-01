// The authored full-frame picture owns the screen. Navigation returns when the
// viewer interacts and stays available for keyboard users and paused playback.
export function createFilmChrome({host,schedule=setTimeout,cancel=clearTimeout,idleMs=2400}){
 let enabled=false,playing=false,timer=null;
 const clear=()=>{if(timer!==null)cancel(timer);timer=null;};
 const keyboardFocus=()=>{
  const active=host.ownerDocument.activeElement;
  return !!active&&host.contains(active)&&active.matches(':focus-visible');
 };
 function idle(){
  clear();if(!enabled||!playing)return;
  timer=schedule(()=>{timer=null;if(!keyboardFocus())host.dataset.controlsVisible='false';},idleMs);
 }
 function reveal(){
  if(!enabled)return;
  host.dataset.controlsVisible='true';idle();
 }
 for(const event of ['pointermove','pointerdown','keydown','focusin'])host.addEventListener(event,reveal);
 host.addEventListener('focusout',idle);
 return {update({story,started,playing:active}){
  clear();enabled=story?.programme?.visualTreatment==='finished-film'&&story.programme.pictureTreatment==='full-frame-v2';
  playing=!!(started&&active);
  host.dataset.pictureTreatment=enabled?'full-frame-v2':'';
  host.dataset.controlsVisible='true';
  idle();
 }};
}
