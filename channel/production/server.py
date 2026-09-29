"""Serve Bearing locally and refresh bounded source briefs in the background."""
import argparse, json, os, re, subprocess, sys, threading, time, webbrowser
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
stop=threading.Event()
status={'state':'starting','lastRun':None,'detail':'Current edition is available while updates are prepared.'}
status_lock=threading.Lock()

class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        self._byte_range=None
        path=Path(self.translate_path(self.path))
        requested=self.headers.get('Range')
        if not requested or not path.is_file() or path.suffix.lower() not in ('.mp3','.mp4','.wav'):
            return super().send_head()
        size=path.stat().st_size
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested.strip())
        start=end=0
        if match and any(match.groups()):
            first,last=match.groups()
            start=int(first) if first else max(0,size-int(last))
            end=min(size-1,int(last)) if first and last else size-1
        if not match or not any(match.groups()) or start>=size or start>end or (not match[1] and match[2]=='0'):
            self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return None
        source=path.open('rb');self._byte_range=(start,end)
        self.send_response(206)
        self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length',str(end-start+1))
        self.send_header('Last-Modified',self.date_time_string(path.stat().st_mtime))
        self.end_headers();return source
    def copyfile(self,source,outputfile):
        if self._byte_range is None:return super().copyfile(source,outputfile)
        start,end=self._byte_range;source.seek(start);remaining=end-start+1
        while remaining:
            chunk=source.read(min(65536,remaining))
            if not chunk:break
            outputfile.write(chunk);remaining-=len(chunk)
    def do_GET(self):
        if self.path.split('?')[0]=='/api/production':
            with status_lock:data=json.dumps(status).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        super().do_GET()
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        if self.path.split('?')[0].endswith(('.mp3','.mp4','.wav')):self.send_header('Accept-Ranges','bytes')
        if self.path.split('?')[0].endswith(('.json','.js','.css','.html')) or self.path=='/':self.send_header('Cache-Control','no-cache')
        super().end_headers()

def refresh(minutes):
    if stop.wait(5):return
    while not stop.is_set():
        with status_lock:status.update(state='checking',detail='Checking approved source feeds.')
        try:
            process=subprocess.run([sys.executable,str(ROOT/'production'/'pipeline.py'),'auto','--limit','4'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=600)
            with status_lock:status.update(detail='Preparing fresh headline videos. The current story keeps playing.')
            video=subprocess.run([sys.executable,str(ROOT/'production'/'latest_video.py'),'--limit','8'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=600)
            programme=subprocess.run([sys.executable,str(ROOT/'production'/'produce_programmes.py')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=600)
            exit_code=process.returncode or video.returncode or programme.returncode
            run={'completedAt':datetime.now(timezone.utc).isoformat(),'exitCode':exit_code,'output':process.stdout[-10000:],'error':process.stderr[-3000:],'headlineVideoOutput':video.stdout[-5000:],'headlineVideoError':video.stderr[-3000:],'programmeOutput':programme.stdout[-5000:],'programmeError':programme.stderr[-3000:]}
            log=ROOT/'production'/'runs'/'last-refresh.json';log.parent.mkdir(parents=True,exist_ok=True);log.write_text(json.dumps(run,indent=2),encoding='utf-8')
            source_path=ROOT/'dist'/'source-status.json'
            health=json.loads(source_path.read_text(encoding='utf-8')) if source_path.exists() else {}
            partial=health.get('healthy',0)<health.get('total',0)
            video_status=ROOT/'production'/'runs'/'latest-video-status.json'
            clips=json.loads(video_status.read_text(encoding='utf-8')) if video_status.exists() else {}
            with status_lock:status.update(state=('partial' if partial or clips.get('errors') else 'idle') if not exit_code else 'held',lastRun=run['completedAt'],healthySources=health.get('healthy'),totalSources=health.get('total'),headlineClips=clips.get('ready'),detail=('Some sources or clips are unavailable. Complete videos remain available.' if partial or clips.get('errors') else 'Source check completed. Fresh headline videos are ready.') if not exit_code else 'Production needs attention. Completed videos remain available.')
        except Exception as exc:
            with status_lock:status.update(state='held',lastRun=datetime.now(timezone.utc).isoformat(),detail='Update unavailable. The last complete edition is retained.')
        if stop.wait(minutes*60):return

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8796);parser.add_argument('--refresh-minutes',type=int,default=1);parser.add_argument('--no-refresh',action='store_true');parser.add_argument('--open-browser',action='store_true');args=parser.parse_args()
    runtime=ROOT/'production'/'runtime.json'
    if runtime.exists():
        settings=json.loads(runtime.read_text(encoding='utf-8'))
        if settings.get('modelDir'):os.environ['CURRENT_PIPER_MODEL_DIR']=settings['modelDir']
        if settings.get('ffmpeg'):os.environ['CURRENT_FFMPEG']=settings['ffmpeg']
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(ROOT/'dist')))
    if not args.no_refresh:threading.Thread(target=refresh,args=(max(1,args.refresh_minutes),),daemon=True).start()
    else:status.update(state='preview',detail='Automatic refresh is disabled in this preview.')
    print(f'Bearing is ready at http://127.0.0.1:{args.port}',flush=True)
    print('Automatic local production enabled.' if not args.no_refresh else 'Preview only.',flush=True)
    if args.open_browser:threading.Timer(.5,lambda:webbrowser.open(f'http://127.0.0.1:{args.port}')).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:stop.set();server.server_close()

if __name__=='__main__':main()
