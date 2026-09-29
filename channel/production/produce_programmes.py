"""Compose source-bound studio programmes; retain source editions and prior renders."""
import argparse, hashlib, json, os, subprocess, wave
from pathlib import Path
import numpy as np
import pipeline
import editorial
import broadcast
import scriptdesk

DIST=pipeline.DIST
WORK=pipeline.WORK
STYLE='studio-programme-v4.1-narration-cues'
TRANSITION_LEAD=1.8
TRANSITION_TAIL=1.8
IDENT_DURATION=4.5
OUTRO_DURATION=4.5
def sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def read(path,default):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
def asset(value):
    path=(DIST/value).resolve()
    if not path.is_relative_to(DIST.resolve()) or not path.is_file():raise ValueError('Missing or unsafe media asset')
    return path

def make_sounds():
    target=DIST/'assets'/'studio';target.mkdir(parents=True,exist_ok=True)
    rate=44100
    for name,length in [('ident',1.5),('sweep',1.5),('resolve',1.5)]:
        path=target/f'{name}-v2.wav'
        if path.exists():continue
        t=np.arange(int(rate*length))/rate
        envelope=np.sin(np.pi*t/length)**2
        if name=='ident':signal=(.11*np.sin(2*np.pi*196*t)+.07*np.sin(2*np.pi*294*t)+.045*np.sin(2*np.pi*392*t))*envelope
        elif name=='resolve':signal=(.055*np.sin(2*np.pi*294*t)+.035*np.sin(2*np.pi*392*t))*envelope
        else:
            rng=np.random.default_rng(24);noise=rng.normal(0,.11,len(t));smooth=np.convolve(noise,np.ones(13)/13,mode='same')
            signal=(smooth+.025*np.sin(2*np.pi*(145*t+170*t*t)))*envelope
        pcm=(signal*32767).astype('<i2')
        with wave.open(str(path),'wb') as handle:handle.setnchannels(1);handle.setsampwidth(2);handle.setframerate(rate);handle.writeframes(pcm.tobytes())

def validate_plan(story,plan):
    if story.get('status')!='ready':raise ValueError('Underlying story is not ready')
    if plan.get('sourceScriptSha256')!=sha(story['script']):raise ValueError('Source script changed; presentation needs review')
    for field in ('title','why','summary','lookAhead'):
        if not isinstance(plan.get(field),str) or not plan[field].strip():raise ValueError(f'Missing {field}')
    if not 2<=len(plan.get('beats',[]))<=4:raise ValueError('A story needs two to four grounded visual beats')
    asset(story['image']);asset(story['video'])
    if story.get('visual',{}).get('storyId')!=story['id']:raise ValueError('Story-specific visual binding is missing')

def produce_story(story,plan,settings):
    from speech import synthesize,provider_fingerprint
    validate_plan(story,plan)
    speech_provider=plan.get('speechProvider','piper-local-cpu')
    speech_fingerprint=provider_fingerprint(speech_provider,settings['modelDir'])
    renderer_revision={p:broadcast.file_hash(DIST/p) for p in ('studio.js','studio.css','directed.js','directed.css','us-states.js')}
    renderer_revision['assembler']=broadcast.file_hash(Path(__file__))
    renderer_revision['broadcast']=broadcast.file_hash(WORK/'broadcast.py')
    identity=sha(json.dumps([STYLE,story['id'],plan,story['image'],story['video'],speech_fingerprint,renderer_revision],sort_keys=True))[:20]
    folder=WORK/'runs'/'programmes'/identity;folder.mkdir(parents=True,exist_ok=True)
    brief=scriptdesk.production_brief(story,plan)
    brief_path=folder/f'editorial-brief-{scriptdesk.fingerprint(brief)[:12]}.json'
    if not brief_path.exists():pipeline.write_json(brief_path,brief)
    record=folder/'programme.json';cached=read(record,{})
    if cached and broadcast.cache_valid(folder,cached):return cached
    run=broadcast.Run(folder,story,identity)
    try:
        scripts=broadcast.write_and_edit(run,story,plan)
        voices={};all_clips={}
        for voice in ('warm','measured'):
            clips={}
            for phase,script in scripts.items():
                path=folder/f'{voice}-{phase}-{sha(script+speech_fingerprint)[:10]}.mp3'
                # Re-time existing verified speech; preserve old mixes and avoid synthesizing it again.
                if not path.exists():
                    patterns=[path.name]
                    # Earlier reviewed Piper clips used the script hash alone. Their
                    # performance is unchanged; retain it when upgrading the renderer.
                    if speech_provider=='piper-local-cpu':patterns.insert(0,f'{voice}-{phase}-{sha(script)[:10]}.mp3')
                    candidates=[prior for pattern in patterns for prior in (WORK/'runs'/'programmes').glob(f'*/{pattern}')]
                    for prior in candidates:
                        prior_meta=read(prior.with_suffix('.provenance.json'),{})
                        if prior_meta.get('provider')==speech_provider and prior_meta.get('scriptSha256')==sha(script) and prior_meta.get('sha256')==hashlib.sha256(prior.read_bytes()).hexdigest():
                            path=prior;break
                meta=read(path.with_suffix('.provenance.json'),{})
                if not(path.exists() and meta.get('provider')==speech_provider and meta.get('scriptSha256')==sha(script) and meta.get('sha256')==hashlib.sha256(path.read_bytes()).hexdigest()):
                    if path.exists():path=folder/f'{path.stem}-retry-{os.urandom(3).hex()}.mp3'
                    meta=synthesize(script,voice,path,settings['modelDir'],provider=speech_provider)
                clips[phase]=(path,meta)
            all_clips[voice]=clips
        run.finish('tts',voices={voice:{phase:{'path':str(path),'sha256':meta['sha256'],'duration':meta['duration']} for phase,(path,meta) in clips.items()} for voice,clips in all_clips.items()})
        visual_composition=broadcast.visuals(run,story,plan)
        music=broadcast.create_music(run,settings,plan)
        timing={'ident':IDENT_DURATION,'outro':OUTRO_DURATION,'lead':TRANSITION_LEAD,'tail':TRANSITION_TAIL,**plan.get('timing',{})}
        if any(not isinstance(v,(int,float)) or v<0 for v in timing.values()):raise ValueError('Invalid programme timing')
        deliveries=[]
        for voice,clips in all_clips.items():
            chapters=[{'kind':'ident','label':'Bearing','start':0,'end':timing['ident']}];cursor=timing['ident'];captions=[];word_timings=[];delays=[]
            for phase,label in [('opening','Why it matters'),('story','The story'),('closing','What to watch')]:
                meta=clips[phase][1];start=cursor;audio_start=start+timing['lead']
                cursor=audio_start+meta['duration']+timing['tail']
                chapters.append({'kind':phase,'label':plan.get('chapterLabels',{}).get(phase,label),'start':round(start,3),'end':round(cursor,3)})
                captions.extend([{**c,'start':round(c['start']+audio_start,5),'end':round(c['end']+audio_start,5)} for c in meta['captions']])
                word_timings.extend([{**c,'start':round(c['start']+audio_start,5),'end':round(c['end']+audio_start,5)} for c in meta.get('wordTimings',[])])
                delays.append(round(audio_start*1000))
            chapters.append({'kind':'outro','label':'Up next','start':round(cursor,3),'end':round(cursor+timing['outro'],3)});duration=cursor+timing['outro']
            if duration>plan.get('maxDuration',160):raise ValueError(f'Programme exceeds its reviewed duration budget: {duration:.2f}s')
            output=DIST/'assets'/'studio'/f'{identity}-{voice}.mp3';temp=folder/f'{voice}-mix.mp3'
            command=[settings['ffmpeg'],'-hide_banner','-nostdin','-v','error']
            for path,meta in clips.values():command+=['-i',str(path)]
            filters=[f'[{i}:a]adelay={delay}:all=1[a{i}]' for i,delay in enumerate(delays)]
            filters.append(f'[a0][a1][a2]amix=inputs=3:normalize=0,apad,atrim=duration={duration},alimiter=limit=0.95:level=false[out]')
            command+=['-filter_complex',';'.join(filters),'-map','[out]','-c:a','libmp3lame','-b:a','128k','-y',str(temp)]
            subprocess.run(command,check=True,capture_output=True,timeout=90)
            subprocess.run([settings['ffmpeg'],'-v','error','-xerror','-i',str(temp),'-f','null','-'],check=True,capture_output=True,timeout=60)
            if not 10<duration<160 or captions[-1]['end']>duration:raise ValueError('Programme duration or captions invalid')
            deliveries.append((temp,output))
            voices[voice]={'audio':output.relative_to(DIST).as_posix(),'duration':round(duration,3),'captions':captions,'chapters':chapters,'sha256':hashlib.sha256(temp.read_bytes()).hexdigest(),'fullDecodePassed':True,'provider':speech_provider,'voiceName':clips['story'][1].get('voiceName'), 'scriptSha256':sha(' '.join(scripts.values()))}
            if word_timings:voices[voice]['wordTimings']=word_timings
            cues=broadcast.timed_beats(plan['beats'],captions,next(c for c in chapters if c['kind']=='story'),word_timings)
            if cues:voices[voice]['visualCues']=cues
            if plan.get('closingReveals'):voices[voice]['closingCues']=broadcast.timed_reveals(plan['closingReveals'],captions,next(c for c in chapters if c['kind']=='closing'),word_timings)
            if plan.get('openingReveals'):voices[voice]['openingCues']=broadcast.timed_reveals(plan['openingReveals'],captions,next(c for c in chapters if c['kind']=='opening'),word_timings)
        # No published delivery is touched until both voices, all cues and the duration gate pass.
        for temporary,target in deliveries:os.replace(temporary,target)
        result={**story,'format':'studio-programme','programmeVersion':identity,'title':plan['title'],'displayTitle':plan['title'],'script':' '.join(scripts.values()),'voices':voices,'programme':{k:plan[k] for k in ('why','summary','lookAhead','beats')},'sourceScriptSha256':plan['sourceScriptSha256'],'builtAt':pipeline.stamp(),'music':music,'production':{'pipeline':'broadcast-v1','visualDecision':'mixture','renderer':'studio.js','sourceBound':True,'compositionHash':sha(json.dumps(visual_composition,sort_keys=True))}}
        for key in ('visualTreatment','soundTreatment','openingReveals','closingReveals','chapterLabels','maxDuration','editorialTiming'):
            if plan.get(key):result['programme'][key]=plan[key]
        result['programme']['editorialTiming']=broadcast.editorial_timing(story,plan,scripts)
        if plan.get('visualTreatment')=='directed':
            result['visualDisclosure']=plan.get('visualDisclosure','Original Bearing explanatory graphics, with licensed media credited when shown.')
            result['editorialNote']=plan.get('editorialNote',story.get('editorialNote',''))
        run.finish('assemble',voices={v:{'audio':t['audio'],'duration':t['duration'],'sha256':t['sha256'],'fullDecodePassed':t['fullDecodePassed']} for v,t in voices.items()},delivery='Timed browser composition of voice, motion video, generated graphics and ducked music; one story per playlist entry')
        pipeline.write_json(record,result);return result
    except Exception as exc:
        run.hold(exc)
        raise

def produce(only=None):
    settings=read(WORK/'runtime.json',{})
    os.environ['CURRENT_PIPER_MODEL_DIR']=settings['modelDir'];os.environ['CURRENT_FFMPEG']=settings['ffmpeg']
    make_sounds();source=read(DIST/'edition.json',{'stories':[]});plans=read(WORK/'programme-plans.json',{'stories':[]})['stories']
    reporting=read(DIST/'reporting.json',{'items':[]})['items'];reports={s['id']:s for s in reporting}
    previous=read(DIST/'programmes.json',{})
    retained={s['id']:s for s in previous.get('stories',[])}
    if only and not any(s['id']==only for s in source['stories']):raise ValueError('Selected story does not exist')
    output=[];held=[]
    for story in source['stories']:
        if only and story['id']!=only:
            if story['id'] in retained:output.append(retained[story['id']])
            continue
        if story['id'] not in plans:
            held.append({'id':story['id'],'reason':'Story plan required'})
            if story['id'] in retained:output.append(retained[story['id']])
            continue
        try:
            complete=produce_story(story,plans[story['id']],settings)
            report=reports.get(story['id']);complete={**complete,'publishedTime':report.get('publishedTime') if report else story.get('publishedTime')}
            complete['coverage']=report.get('coverage') if report else None
            complete['editorial']=editorial.assess(complete);output.append(complete);print(json.dumps({'programme':story['id'],'seconds':complete['voices']['warm']['duration']}),flush=True)
        except Exception as exc:
            held.append({'id':story['id'],'reason':str(exc)[:300]})
            if story['id'] in retained:output.append(retained[story['id']])
    # A retained delivery can stay playable after a failed rebuild, but its old
    # current-news review cannot silently remain valid indefinitely.
    for complete in output:
        timing=complete.get('programme',{}).get('editorialTiming')
        if timing and timing.get('mode')=='current':
            try:complete['programme']['editorialTiming']=broadcast.validate_editorial_timing(timing)
            except ValueError as exc:complete['programme']['editorialTiming']={**timing,'liveEligible':False,'label':'Context — review needed','holdReason':str(exc)}
    version=sha(json.dumps([(s['id'],s['programmeVersion'],s.get('publishedTime'),s.get('editorial'),s.get('coverage'),s.get('programme',{}).get('editorialTiming')) for s in output]))
    if version!=previous.get('version'):
        if previous:pipeline.write_json(WORK/'runs'/'programme-editions'/f"{previous['version']}.json",previous)
        pipeline.write_json(DIST/'programmes.json',{'edition':source.get('edition'),'version':version,'builtAt':pipeline.stamp(),'stories':output})
    for complete in output:broadcast.publish_record(complete)
    ready_ids={s['id'] for s in output}
    pipeline.write_json(WORK/'runs'/'broadcast-queue.json',{'checkedAt':pipeline.stamp(),'stages':broadcast.STAGES,'published':len(output),'waiting':[{'id':s['id'],'title':s['title'],'source':s['source'],'editorial':s.get('editorial'),'nextStage':'write_script','reason':'Needs a source-supported broadcast script and accuracy/style review; headline readout is not a full package'} for s in editorial.rank(reporting,32) if s['id'] not in ready_ids],'automationBoundary':'Reviewed source-bound plans run through local TTS, visual composition, original procedural music, assembly checks and atomic publication. New factual scripts and bespoke visual assets are held for editorial/art review.'})
    pipeline.write_json(WORK/'runs'/'programme-status.json',{'checkedAt':pipeline.stamp(),'ready':len(output),'held':held})
    print(json.dumps({'ready':len(output),'held':held}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--only');args=parser.parse_args()
    with pipeline.production_lock():produce(args.only)
