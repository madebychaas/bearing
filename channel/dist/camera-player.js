let apiPromise;
export function loadYouTubeAPI(){
 if(window.YT?.Player)return Promise.resolve(window.YT);
 if(apiPromise)return apiPromise;
 apiPromise=new Promise((resolve,reject)=>{
  const script=document.createElement('script');script.src='https://www.youtube.com/iframe_api';
  const previous=window.onYouTubeIframeAPIReady;
  const finish=()=>{clearTimeout(timer);resolve(window.YT);};
  const fail=()=>{clearTimeout(timer);script.remove();apiPromise=null;reject(Error('The camera player could not connect to YouTube.'));};
  const timer=setTimeout(fail,15000);
  window.onYouTubeIframeAPIReady=()=>{previous?.();finish();};
  script.onerror=fail;document.head.append(script);
 });
 return apiPromise;
}

export function cameraError(code){
 if(code===100)return 'This camera broadcast is no longer available. Check the provider for its replacement.';
 if(code===101||code===150)return 'The provider does not allow this broadcast to play here. Open it at the source.';
 if(code===153)return 'YouTube could not verify this browser’s player identity. Open the camera at the source.';
 return 'The camera could not play in this browser. Try again or open it at the source.';
}

// Only a provider PLAYING event confirms playback. Loading an iframe does not.
export function startCamera({screen,videoId,onStatus,loadAPI=loadYouTubeAPI,timeoutMs=20000}){
 let closed=false,player=null,frame=null;
 const status=(state,text)=>{if(!closed)onStatus(state,text);};
 const timer=setTimeout(()=>status('unavailable','The camera has not started. Try again or open it at the source.'),timeoutMs);
 status('loading','Connecting to the camera…');
 loadAPI().then(YT=>{
  if(closed)return;
  frame=document.createElement('iframe');
  const url=new URL(`https://www.youtube.com/embed/${videoId}`);
  url.search=new URLSearchParams({enablejsapi:'1',origin:location.origin,autoplay:'1',mute:'1',playsinline:'1',rel:'0'});
  frame.src=url.href;frame.title='Official camera player';frame.referrerPolicy='strict-origin-when-cross-origin';
  frame.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';frame.allowFullscreen=true;
  screen.append(frame);
  player=new YT.Player(frame,{events:{
   onReady(event){if(closed)return;event.target.mute();event.target.playVideo();},
   onStateChange(event){
    if(closed)return;
    if(event.data===1){clearTimeout(timer);status('playing','Camera playing · Check the provider’s on-screen live status.');}
    else if(event.data===2){clearTimeout(timer);status('paused','Camera paused. Use the player to resume.');}
    else if(event.data===0){clearTimeout(timer);status('ended','This broadcast has ended. Check the source for the next live view.');}
    else if(event.data===3)status('buffering','Camera buffering…');
   },
   onAutoplayBlocked(){clearTimeout(timer);status('blocked','Press Play inside the camera to start. Your browser blocked automatic playback.');},
   onError(event){clearTimeout(timer);status('unavailable',cameraError(event.data));}
  }});
 }).catch(()=>{clearTimeout(timer);status('unavailable','The camera player could not connect. Try again or open it at the source.');});
 return ()=>{closed=true;clearTimeout(timer);player?.destroy();frame?.remove();};
}
