"""Produce one reviewed, immutable finished story without rebuilding legacy cuts.

The input packet is an editorial approval, not an intake feed. Original graphics
come from film_visuals.render; Kokoro, evidence gates and music reuse Bearing's
existing production machinery. Nothing enters films.json until both voices pass.
"""
import argparse, copy, hashlib, json, math, os, re, subprocess, tempfile, wave
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
import broadcast, editorial, film_audio, pipeline
from speech import synthesize, provider_fingerprint

DIST=pipeline.DIST
WORK=pipeline.WORK
PROVIDER='kokoro-local-cpu'
VERSION='bearing-finished-film-v1'


def read(path,default=None):
    return json.loads(Path(path).read_text(encoding='utf-8')) if Path(path).exists() else default


def sha(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()


def web_url(value):
    parsed=urlsplit(value or '')
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
        raise ValueError('Reviewed source and rights links must be ordinary HTTPS URLs')
    return value


def validate_packet(packet):
    story=packet['story'];plan=packet['plan'];visuals=packet['visuals']
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{5,100}',story.get('id','')):raise ValueError('A stable story ID is required')
    if story.get('reviewStatus')!='verified' or not story.get('reviewedAt'):raise ValueError('The story needs an explicit accuracy and editorial review')
    if not all(story.get(key) for key in ('title','script','topic','topicLabel','publishedAt','expiresAt','editorialNote','visualDisclosure')):raise ValueError('The reviewed source packet is incomplete')
    web_url(story.get('source',{}).get('url'))
    if not all(story['source'].get(key) for key in ('name','title')):raise ValueError('Name the supporting reporting')
    if plan.get('sourceScriptSha256')!=sha(story['script']):raise ValueError('Reviewed script hash changed')
    if plan.get('soundTreatment')!='editorial-score':raise ValueError('The finished film needs its reviewed score treatment')
    if not 1<=len(plan.get('beats',[]))<=4:raise ValueError('Review one to four body scenes')
    timing=broadcast.validate_editorial_timing(plan.get('editorialTiming'))
    if timing.get('mode')!='current' or not timing.get('liveEligible'):raise ValueError('This current-news film needs a valid current editorial reason')
    expires=pipeline.date_value(story['expiresAt'])
    if not expires or expires<=datetime.now(timezone.utc):raise ValueError('Current story expiry is missing or already passed')
    published=pipeline.date_value(story.get('publishedTime') or story['publishedAt'])
    if not published or (published-datetime.now(timezone.utc)).total_seconds()>900:raise ValueError('The reviewed report cannot claim a future publication')
    if not 25<=plan.get('maxDuration',45)<=45:raise ValueError('Narration-only finished film budget must be 25–45 seconds')
    rate=plan.get('narrationRate',.93)
    if not isinstance(rate,(float,int)) or not .85<=rate<=1:raise ValueError('Narration performance must preserve a measured pace')
    for pause in plan.get('narrationPauses',[]):
        if pause.get('phase') not in ('opening','story','closing') or not pause.get('after') or not isinstance(pause.get('seconds'),(float,int)) or not .15<=pause['seconds']<=3:raise ValueError('Invalid reviewed narration pause')
    if plan.get('narrationFlow'):
        flow=plan['narrationFlow']
        if not .16<=flow.get('minimumSentenceGap',.20)<=.4 or not .1<=flow.get('minimumPhraseGap',.12)<=.25:raise ValueError('Invalid reviewed narration flow policy')
    if not isinstance(visuals.get('description'),str) or not visuals['description'].strip():raise ValueError('Explain the reviewed visual treatment')
    if not isinstance(visuals.get('assets'),list):raise ValueError('Explicit visual asset review is required, including an empty list for original code graphics')
    for asset in visuals['assets']:
        if asset.get('usageApproved') is not True or asset.get('kind') not in ('original','generated','licensed') or not asset.get('description'):raise ValueError('A visual has not passed its use review')
        value=asset.get('path','');path=(DIST/value).resolve()
        if not isinstance(value,str) or not value.startswith('assets/') or not path.is_relative_to((DIST/'assets').resolve()) or not path.is_file() or broadcast.file_hash(path)!=asset.get('sha256'):raise ValueError('Reviewed visual asset or hash mismatch')
        if asset['kind']=='generated' and not asset.get('prompt'):raise ValueError('Retain the generated visual prompt')
        if asset['kind']=='licensed':
            if not all(asset.get(key) for key in ('sourceUrl','licenseUrl','license','author','courtesy')):raise ValueError('Third-party visuals require permission and a visible courtesy')
            web_url(asset['sourceUrl']);web_url(asset['licenseUrl'])
    return timing


def run_ffmpeg(settings,args,timeout=120):
    return subprocess.run([settings['ffmpeg'],'-hide_banner','-nostdin','-v','error',*map(str,args)],check=True,capture_output=True,timeout=timeout)


def decode(settings,path):
    run_ffmpeg(settings,['-xerror','-i',path,'-f','null','-'])


def pcm(settings,path):
    result=run_ffmpeg(settings,['-i',path,'-ar','24000','-ac','1','-f','f32le','-'])
    return np.frombuffer(result.stdout,dtype='<f4').copy()


def write_wave(path,samples):
    with wave.open(str(path),'wb') as writer:
        writer.setnchannels(1);writer.setsampwidth(2);writer.setframerate(24000)
        writer.writeframes((np.clip(samples,-.999,.999)*32767).astype('<i2').tobytes())


def scale_metadata(meta,rate,duration):
    scaled=copy.deepcopy(meta)
    for field in ('captions','wordTimings'):
        scaled[field]=[{**item,'start':round(item['start']/rate,5),'end':round(item['end']/rate,5)} for item in meta.get(field,[])]
        if scaled[field] and scaled[field][-1]['end']>duration:
            if scaled[field][-1]['end']-duration>.12:raise ValueError('Tempo-adjusted timing exceeds the voice track')
            scaled[field][-1]['end']=round(duration,5)
    scaled.update(duration=duration,performanceRate=rate,timingAdjustment='Model word boundaries scaled by the atempo rate; WSOLA sample rounding is bounded to 120ms')
    return scaled


def insert_narration_pauses(samples,meta,pauses,rate=24000):
    """Add reviewed reading space only inside a quiet inter-sentence gap."""
    updated=copy.deepcopy(meta);audio=np.asarray(samples).copy();evidence=[]
    tokens=lambda value:re.findall(r'[a-z0-9]+',value.lower())
    for pause in pauses:
        seconds=pause.get('seconds',0);target=tokens(pause.get('after',''))
        if not target or not isinstance(seconds,(int,float)) or not .15<=seconds<=3:raise ValueError('Narration pause needs a sentence-ending cue and 0.15–3 seconds')
        matches=[index for index,caption in enumerate(updated['captions'][:-1]) if tokens(caption['text'])[-len(target):]==target and re.search(r'[.!?][\"\u201d\u2019]?$',caption['text'].strip())]
        if len(matches)!=1:raise ValueError('Narration pause must match exactly one complete sentence before another sentence')
        index=matches[0];left=updated['captions'][index]['end'];right=updated['captions'][index+1]['start']
        start=math.ceil(left*rate);end=math.floor(right*rate);window=max(1,round(.015*rate))
        if end-start<window:raise ValueError('Narration pause has no safe inter-sentence gap')
        energy=np.convolve(audio[start:end].astype(np.float64)**2,np.ones(window)/window,mode='valid')
        best=int(np.argmin(energy));rms=math.sqrt(float(energy[best]))
        if rms>.01:raise ValueError('Narration pause would interrupt audible speech')
        offset=start+best+window//2;at=offset/rate;extra=round(seconds*rate);seconds=extra/rate
        for field in ('captions','wordTimings'):
            for item in updated.get(field,[]):
                if item['start']>=at:
                    item['start']=round(item['start']+seconds,5);item['end']=round(item['end']+seconds,5)
                elif item['end']>at:raise ValueError('Narration pause would split a timed spoken word')
        audio=np.concatenate((audio[:offset],np.zeros(extra,dtype=audio.dtype),audio[offset:]))
        evidence.append({'after':pause['after'],'at':round(at,5),'seconds':seconds,'gapRms':round(rms,7)})
    updated['duration']=len(audio)/rate
    if evidence:updated['narrationPauses']=evidence
    return audio,updated


def readable_captions(captions,word_timings):
    """Short exact-text phrases, anchored to actual words, never sentence estimates."""
    output=[]
    for caption in captions:
        words=[word for word in word_timings if caption['start']<=word['start']<caption['end']]
        if ' '.join(word['text'] for word in words)!=' '.join(caption['text'].split()):raise ValueError('Caption words do not match the reviewed sentence')
        group=[]
        def emit():
            output.append({'text':' '.join(word['text'] for word in group),'start':group[0]['start'],'end':group[-1]['end']})
        for word in words:
            if group and (len(group)>=8 or len(' '.join(item['text'] for item in [*group,word]))>52):emit();group=[]
            group.append(word)
            if len(group)>=3 and re.search(r'[,;:]$',word['text']):emit();group=[]
        if group:emit()
    if ' '.join(item['text'] for item in output)!=' '.join(item['text'] for item in captions):raise ValueError('Caption chunking changed the approved copy')
    return output


def build_track(clips,plan):
    timing={'ident':.35,'lead':.1,'tail':.45,'outro':1.1,**plan.get('timing',{})}
    if any(not isinstance(value,(int,float)) or value<0 for value in timing.values()):raise ValueError('Invalid film timing')
    captions=[];words=[];placements=[];pauses=[];silence_edits=[];cursor=timing['ident'];chapters=[{'kind':'ident','label':'Bearing','start':0,'end':round(cursor,3)}]
    for phase,label in [('opening','The shift'),('story','The story'),('closing','What follows')]:
        meta=clips[phase][1];start=cursor;audio_start=start+timing['lead'];cursor=audio_start+meta['duration']+timing['tail']
        chapters.append({'kind':phase,'label':plan.get('chapterLabels',{}).get(phase,label),'start':round(start,3),'end':round(cursor,3)})
        placements.append((clips[phase][0],audio_start))
        captions.extend({**c,'start':round(c['start']+audio_start,5),'end':round(c['end']+audio_start,5)} for c in meta['captions'])
        words.extend({**c,'start':round(c['start']+audio_start,5),'end':round(c['end']+audio_start,5)} for c in meta.get('wordTimings',[]))
        pauses.extend({**pause,'phase':phase,'at':round(pause['at']+audio_start,5)} for pause in meta.get('narrationPauses',[]))
        silence_edits.extend({**edit,'phase':phase} for edit in meta.get('silenceEdits',[]))
    duration=math.ceil((cursor+timing['outro'])*30)/30
    if not 10<duration<=plan.get('maxDuration',45):raise ValueError(f'Film exceeds the reviewed duration budget: {duration:.2f}s')
    chapters.append({'kind':'outro','label':'Up next','start':round(cursor,3),'end':round(duration,3)})
    track={'duration':round(duration,3),'captions':captions,'wordTimings':words,'chapters':chapters,'provider':PROVIDER,'voiceName':clips['story'][1]['voiceName'],'performanceRate':plan.get('narrationRate',.93)}
    if pauses:track['narrationPauses']=pauses
    if plan.get('narrationFlow'):track.update(silenceEdits=silence_edits,narrationFlow=plan['narrationFlow'])
    for name,phase,values in [('openingCues','opening',plan.get('openingReveals')),('closingCues','closing',plan.get('closingReveals'))]:
        if values:track[name]=broadcast.timed_reveals(values,captions,next(c for c in chapters if c['kind']==phase),words)
    cues=broadcast.timed_beats(plan['beats'],captions,next(c for c in chapters if c['kind']=='story'),words)
    if cues:track['visualCues']=cues
    track['captions']=readable_captions(captions,words)
    return track,placements


def assemble_narration(settings,placements,duration,path):
    samples=np.zeros(round(duration*24000),dtype=np.float64)
    for source,start in placements:
        clip=pcm(settings,source);offset=round(start*24000)
        if offset+len(clip)>len(samples):raise ValueError('Voice clip extends beyond the film')
        samples[offset:offset+len(clip)]+=clip
    if not np.isfinite(samples).all() or np.max(np.abs(samples))>1:raise ValueError('Narration assembly has invalid or clipped samples')
    write_wave(path,samples);return samples


def score_mix(settings,narration,track,music,path):
    mixed,evidence=film_audio.mix(narration,track,*(pcm(settings,DIST/music[key]) for key in ('drift','signature','handoff')))
    write_wave(path,mixed);return evidence


def subtitle_time(seconds):
    value=round(seconds*1000);hours,value=divmod(value,3600000);minutes,value=divmod(value,60000);whole,millis=divmod(value,1000)
    return f'{hours:02}:{minutes:02}:{whole:02},{millis:03}'


def subtitles(path,captions):
    path.write_text('\n\n'.join(f"{i}\n{subtitle_time(c['start'])} --> {subtitle_time(c['end'])}\n{c['text']}" for i,c in enumerate(captions,1))+'\n',encoding='utf-8')


def cache_valid(record):
    try:
        return bool(record.get('story')) and bool(record.get('assets')) and all((DIST/asset['path']).is_file() and broadcast.file_hash(DIST/asset['path'])==asset['sha256'] for asset in record['assets'])
    except (KeyError,TypeError,OSError):return False


def deliver_asset(source,target,digest):
    """Only complete, verified files may claim an immutable delivery name."""
    if target.exists():
        if broadcast.file_hash(target)!=digest:raise ValueError('Immutable film output differs; preserve it under a new production identity')
        return
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent,prefix=f'.{target.name}.',suffix='.tmp',delete=False) as writer:
            temporary=Path(writer.name);writer.write(source.read_bytes());writer.flush();os.fsync(writer.fileno())
        if broadcast.file_hash(temporary)!=digest:raise ValueError('Staged film asset failed integrity verification')
        if target.exists():
            if broadcast.file_hash(target)!=digest:raise ValueError('Immutable film output differs; preserve it under a new production identity')
        else:os.replace(temporary,target)
    finally:
        if temporary and temporary.exists():temporary.unlink()


def create_film_music(run,settings,tracks):
    seconds=max(track['duration'] for track in tracks.values())+.25
    assets={};durations={'drift':seconds,'piano':seconds,'signature':.28,'handoff':.28,'bridge':1.5}
    for style,duration in durations.items():
        wav=run.folder/f'film-score-{style}.wav';mp3=run.folder/f'film-score-{style}.mp3'
        write_wave(wav,film_audio.editorial_score(style,duration))
        run_ffmpeg(settings,['-i',wav,'-c:a','libmp3lame','-b:a','128k','-y',mp3]);decode(settings,mp3)
        target=DIST/'assets'/'studio'/f"score-{run.data['version']}-{style}.mp3"
        deliver_asset(mp3,target,broadcast.file_hash(mp3));assets[style]=target.relative_to(DIST).as_posix()
    pipeline.write_json(run.folder/'music.json',{'assets':assets,'composer':'Original Bearing dry low-register pulse and muted-key variation','rights':'Original composition and synthesis; no samples, borrowed music or external services','profile':'restrained-editorial-v2','durations':durations,'treatment':'editorial-score','sha256':{key:broadcast.file_hash(DIST/value) for key,value in assets.items()}})
    run.finish('create_music',artifact='music.json',method='Brief dry opening accent; finite sparse editorial pulse and muted-key option underneath intact dialogue')
    return assets


def publish(story,run):
    previous=read(DIST/'films.json',{'stories':[]});entries=[entry for entry in previous['stories'] if entry['id']!=story['id']]+[story]
    version=sha(json.dumps([(entry['id'],entry['programmeVersion']) for entry in entries],sort_keys=True))
    if previous.get('version')!=version:
        if previous.get('version'):pipeline.write_json(WORK/'runs'/'film-editions'/f"{previous['version']}.json",previous)
        pipeline.write_json(DIST/'films.json',{'schema':1,'edition':datetime.now(timezone.utc).date().isoformat(),'version':version,'builtAt':pipeline.stamp(),'stories':entries})
    if len(run.data['stages'])==8:run.finish('publish',artifact='dist/films.json',entryPolicy='One complete story; joins the native playlist at a story boundary')
    run.data['state']='published';pipeline.write_json(run.path,run.data)


def finish_delivery(packet,story,run,publish_result,completion_guard):
    """Recheck editorial authority at the last boundary, including cached output."""
    validate_packet(packet)
    if completion_guard:completion_guard()
    if publish_result:publish(story,run)
    else:
        # A producer preview is a complete asset, not a playlist publication.
        # Preserve a pre-existing published run if this packet is only previewed.
        if run.data.get('state')!='published':
            run.data.update(state='produced',completedAt=pipeline.stamp(),publication='Preview only; not admitted to films.json')
            pipeline.write_json(run.path,run.data)
    return story


def produce(packet,publish_result=True,completion_guard=None):
    if completion_guard:completion_guard()
    editorial_timing=validate_packet(packet);story=copy.deepcopy(packet['story']);plan=copy.deepcopy(packet['plan']);settings=read(WORK/'runtime.json')
    os.environ['CURRENT_FFMPEG']=settings['ffmpeg']
    renderer_path=WORK/'film_visuals.py'
    if not renderer_path.is_file():raise RuntimeError('The reviewed finished-film picture renderer is unavailable')
    fingerprints={path.name:broadcast.file_hash(path) for path in (Path(__file__),renderer_path,WORK/'film_audio.py',WORK/'broadcast.py',WORK/'speech.py',WORK/'speech_kokoro.py')}
    identity=sha(json.dumps([VERSION,packet,fingerprints,provider_fingerprint(PROVIDER,settings['modelDir'])],sort_keys=True))[:20]
    folder=WORK/'runs'/'films'/identity;folder.mkdir(parents=True,exist_ok=True)
    output=DIST/'assets'/'films'/identity;output.mkdir(parents=True,exist_ok=True)
    record_path=folder/'film.json';cached=read(record_path,{})
    if cache_valid(cached):
        run=broadcast.Run(folder,story,identity);run.data=read(run.path)
        return finish_delivery(packet,cached['story'],run,publish_result,completion_guard)
    run=broadcast.Run(folder,story,identity)
    pipeline.write_json(folder/'reviewed-packet.json',packet)
    try:
        scripts=broadcast.write_and_edit(run,story,plan);tracks={};narrations={};rate=plan.get('narrationRate',.93);full_script=' '.join(scripts.values())
        for voice in ('warm','measured'):
            clips={}
            for phase,script in scripts.items():
                source=folder/f'{voice}-{phase}-native.mp3';meta=read(source.with_suffix('.provenance.json'),{})
                if not source.exists():meta=synthesize(script,voice,source,settings['modelDir'],provider=PROVIDER)
                if meta.get('scriptSha256')!=sha(script) or meta.get('sha256')!=broadcast.file_hash(source):raise ValueError('Retained native narration no longer matches the reviewed script')
                paced=folder/f'{voice}-{phase}-paced.wav'
                run_ffmpeg(settings,['-i',source,'-af',f'atempo={rate}','-ar','24000','-ac','1','-c:a','pcm_s16le','-y',paced])
                with wave.open(str(paced),'rb') as handle:duration=handle.getnframes()/handle.getframerate()
                paced_meta=scale_metadata(meta,rate,duration)
                if plan.get('narrationFlow'):
                    flowing,paced_meta=film_audio.compact_silence(pcm(settings,paced),paced_meta,plan['narrationFlow']);write_wave(paced,flowing)
                pauses=[pause for pause in plan.get('narrationPauses',[]) if pause.get('phase')==phase]
                if pauses:
                    held,paced_meta=insert_narration_pauses(pcm(settings,paced),paced_meta,pauses);write_wave(paced,held)
                clips[phase]=(paced,paced_meta)
            track,placements=build_track(clips,plan);voice_path=folder/f'{voice}-narration.wav';narrations[voice]=assemble_narration(settings,placements,track['duration'],voice_path)
            staged_mp3=folder/f'{voice}-narration.mp3';run_ffmpeg(settings,['-i',voice_path,'-c:a','libmp3lame','-b:a','128k','-y',staged_mp3]);decode(settings,staged_mp3)
            track.update(scriptSha256=sha(full_script),sha256=broadcast.file_hash(staged_mp3),fullDecodePassed=True);tracks[voice]=track
        run.finish('tts',provider=PROVIDER,performanceRate=rate,method='Whole-sentence native Kokoro; pitch-preserving per-story atempo with proportionally adjusted word timing',voices={voice:{'duration':track['duration'],'voiceName':track['voiceName']} for voice,track in tracks.items()})
        pipeline.write_json(folder/'visual-plan.json',{'description':packet['visuals']['description'],'assets':packet['visuals']['assets'],'beats':plan['beats'],'opening':plan.get('openingReveals',[]),'closing':plan.get('closingReveals',[]),'rendererSha256':fingerprints['film_visuals.py']})
        run.finish('plan_visuals',artifact='visual-plan.json',method='Reviewed story-specific scenes and licensed or original assets')
        from film_visuals import render
        render_evidence={}
        for voice,track in tracks.items():
            render_evidence[voice]=render(packet,track,folder/f'{voice}-picture.mp4',folder/f'{voice}-poster.png',settings['ffmpeg'])
            decode(settings,folder/f'{voice}-picture.mp4')
        pipeline.write_json(folder/'visual-composition.json',{'renderers':fingerprints,'renders':render_evidence,'assets':packet['visuals']['assets']})
        run.finish('create_visuals',artifact='visual-composition.json',method='Full-frame original animated story composition, separately timed for both voices')
        music=create_film_music(run,settings,tracks);mixes={};deliveries=[];assets=[]
        for voice,track in tracks.items():
            mixed=folder/f'{voice}-mixed.wav';mixes[voice]=score_mix(settings,narrations[voice],track,music,mixed)
            subtitle=folder/f'{voice}.srt';subtitles(subtitle,track['captions']);movie=folder/f'{voice}-finished.mp4'
            run_ffmpeg(settings,['-i',folder/f'{voice}-picture.mp4','-i',mixed,'-i',subtitle,'-map','0:v:0','-map','1:a:0','-map','2:s:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-c:s','mov_text','-metadata:s:s:0','language=eng','-t',str(track['duration']),'-movflags','+faststart','-y',movie],timeout=180)
            decode(settings,movie)
            if abs(pipeline.media_duration(movie)-track['duration'])>.12:raise ValueError('Completed picture and narration durations disagree')
            for source,name in [(movie,f'{voice}.mp4'),(folder/f'{voice}-narration.mp3',f'{voice}.mp3'),(folder/f'{voice}-poster.png',f'{voice}-poster.png'),(subtitle,f'{voice}.srt')]:
                target=output/name;digest=broadcast.file_hash(source)
                if target.exists() and broadcast.file_hash(target)!=digest:raise ValueError('Immutable film output differs; preserve it under a new production identity')
                deliveries.append((source,target));assets.append({'path':target.relative_to(DIST).as_posix(),'sha256':digest})
            track.update(audio=(output/f'{voice}.mp3').relative_to(DIST).as_posix(),video=(output/f'{voice}.mp4').relative_to(DIST).as_posix(),videoSha256=broadcast.file_hash(movie),subtitles=(output/f'{voice}.srt').relative_to(DIST).as_posix())
        # Recheck pinned selection evidence before giving staged work delivery paths.
        validate_packet(packet)
        if completion_guard:completion_guard()
        # Neither the manifest nor any existing story is touched by a failed render.
        for source,target in deliveries:
            deliver_asset(source,target,broadcast.file_hash(source))
        image=(output/'measured-poster.png').relative_to(DIST).as_posix();video=tracks['measured']['video']
        programme={key:copy.deepcopy(value) for key,value in plan.items() if key in ('why','summary','lookAhead','beats','openingReveals','closingReveals','chapterLabels','maxDuration')}
        programme.update(visualTreatment='finished-film',soundTreatment='editorial-score',editorialTiming=editorial_timing)
        result={**story,'title':plan['title'],'displayTitle':plan['title'],'script':full_script,'status':'ready','format':'studio-programme','programmeVersion':identity,'programme':programme,'voices':tracks,'music':music,'image':image,'video':video,'builtAt':pipeline.stamp(),'sourceScriptSha256':plan['sourceScriptSha256'],'production':{'pipeline':'finished-film-v1','visualDecision':'original produced film','renderer':'film_visuals.py','sourceBound':True,'standaloneMaster':video,'compositionHash':sha(json.dumps(render_evidence,sort_keys=True))}}
        if packet.get('selection'):result['production']['selection']=copy.deepcopy(packet['selection'])
        result['visual']={'scope':'story','storyId':story['id'],'scriptSha256':sha(full_script),'reviewedAt':story['reviewedAt'],'image':image,'video':video,'imageSha256':broadcast.file_hash(DIST/image),'videoSha256':broadcast.file_hash(DIST/video),'alt':packet['visuals']['description']}
        result['editorial']=copy.deepcopy(story.get('editorial')) or editorial.assess(result,packet.get('editorialSource'))
        assets.extend({'path':value,'sha256':broadcast.file_hash(DIST/value)} for value in music.values())
        run.finish('assemble',voices={voice:{'duration':track['duration'],'video':track['video'],'sha256':track['videoSha256'],'fullDecodePassed':True} for voice,track in tracks.items()},mixes=mixes,delivery='Standalone MP4 with mastered sound and optional captions; same muted picture and configurable audio in Bearing')
        # The final guard runs after assembly as well: a hold or source change
        # cannot be cleared by a successful encode or a reusable cache entry.
        pipeline.write_json(record_path,{'story':result,'assets':assets,'fingerprints':fingerprints,'mixes':mixes})
        return finish_delivery(packet,result,run,publish_result,completion_guard)
    except Exception as error:
        run.hold(error);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);args=parser.parse_args()
    settings=read(WORK/'runtime.json');os.environ['CURRENT_FFMPEG']=settings['ffmpeg'];os.environ['CURRENT_PIPER_MODEL_DIR']=settings['modelDir']
    with pipeline.production_lock():
        result=produce(read(args.input));print(json.dumps({'id':result['id'],'version':result['programmeVersion'],'voices':{voice:track['duration'] for voice,track in result['voices'].items()},'master':result['production']['standaloneMaster']}))
