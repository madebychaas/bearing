const make=(tag,cls,text)=>{const e=document.createElement(tag);e.className=cls;if(text)e.textContent=text;return e;};
export async function createCameras({onOpen}){
 const host=document.getElementById('camera-tiles');let active=null;
 try{
  const response=await fetch('cameras.json',{cache:'no-cache'});if(!response.ok)throw Error();const data=await response.json();
  for(const camera of data.cameras){
   if(!/^[A-Za-z0-9_-]{11}$/.test(camera.videoId)||!/^https:\/\//.test(camera.rightsUrl))continue;
   const card=make('article','camera-card'),screen=make('div','camera-screen'),preview=make('button','camera-preview');preview.setAttribute('aria-label',`Open ${camera.title} camera`);
   const image=make('img','');image.src=`https://i.ytimg.com/vi/${camera.videoId}/hqdefault.jpg`;image.alt=`Provider preview of ${camera.title}`;image.loading='lazy';image.onerror=()=>image.remove();
   preview.append(image,make('span','camera-play','▶'),make('span','camera-preview-label','OPEN CAMERA · YOUTUBE'));screen.append(preview);
   const stop=make('button','camera-stop','Close camera');stop.hidden=true;
   const close=()=>{card.classList.remove('is-open');screen.querySelector('iframe')?.remove();preview.hidden=false;stop.hidden=true;};stop.onclick=()=>{close();active=null;};
   preview.onclick=()=>{active?.();onOpen();card.classList.add('is-open');preview.hidden=true;stop.hidden=false;const frame=document.createElement('iframe');frame.src=`https://www.youtube-nocookie.com/embed/${camera.videoId}?autoplay=1&mute=1&playsinline=1`;frame.title=`${camera.provider}: ${camera.title}`;frame.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';frame.allowFullscreen=true;frame.referrerPolicy='strict-origin-when-cross-origin';screen.append(frame);active=close;};
   const content=make('div','camera-copy');content.append(make('span','camera-purpose',camera.purpose),make('h3','',camera.title),make('p','camera-description',camera.description),make('p','camera-availability',camera.availability));
   const links=make('div','camera-links');for(const [title,url] of [[camera.provider,camera.sourceUrl],['Open at source ↗',camera.watchUrl]]){const a=make('a','',title);a.href=url;a.target='_blank';a.rel='noopener noreferrer';links.append(a);}
   const details=make('details','camera-rights'),summary=make('summary','',camera.rightsLabel),rights=make('a','','Provider reuse policy ↗');rights.href=camera.rightsUrl;rights.target='_blank';rights.rel='noopener noreferrer';details.append(summary,make('p','',camera.rightsScope),rights);
   const about=make('details','camera-about'),aboutTitle=make('summary','','About this view');about.append(aboutTitle,content.querySelector('.camera-description'),content.querySelector('.camera-availability'),details);content.append(about,links,stop);card.append(screen,content);host.append(card);
  }
 }catch{host.textContent='Camera listings are temporarily unavailable. Your news playlist is still available.';}
 return {stop(){active?.();active=null;}};
}
