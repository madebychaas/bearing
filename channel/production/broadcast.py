"""Nine-stage, evidence-bound broadcast production records and local music.

The script editor consumes an existing reviewed presentation plan. It does not
pretend that a headline, a hash check, or an LLM is independent fact verification.
"""
import hashlib,json,re,subprocess,wave
from pathlib import Path
import numpy as np
import pipeline

STAGES=['source','write_script','edit_script','tts','plan_visuals','create_visuals','create_music','assemble','publish']
def digest(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()
def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class Run:
    def __init__(self,folder,story,identity):
        self.folder=folder;self.path=folder/'production.json'
        self.data={'schema':1,'id':story['id'],'version':identity,'state':'working','source':story['source'],'stages':[]}
    def finish(self,stage,**evidence):
        if stage!=STAGES[len(self.data['stages'])]:raise ValueError('Production stage out of order')
        self.data['stages'].append({'stage':stage,'completedAt':pipeline.stamp(),**evidence});pipeline.write_json(self.path,self.data)
    def hold(self,reason):
        self.data.update(state='held',heldAt=STAGES[min(len(self.data['stages']),8)],reason=str(reason));pipeline.write_json(self.path,self.data)

def write_and_edit(run,story,plan):
    evidence={'url':story['source']['url'],'sourceTitle':story['source']['title'],'sourceScript':story['script'],'sourceScriptSha256':digest(story['script']),'date':story.get('publishedTime') or story.get('publishedAt') or story.get('dateLabel')}
    if plan.get('review'):evidence['presentationReview']=plan['review']
    pipeline.write_json(run.folder/'source-evidence.json',evidence)
    run.finish('source',artifact='source-evidence.json',sourceScriptSha256=evidence['sourceScriptSha256'])
    scripts={'opening':plan.get('openingNarration',f"{plan['title']}. {plan['why']}"),'story':plan.get('body',story['script']),'closing':plan.get('closingNarration',f"{plan['summary']} What to watch next. {plan['lookAhead']}")}
    pipeline.write_json(run.folder/'script-draft.json',{'scripts':scripts,'method':'Compile the source-bound editorial presentation plan','sourceScriptSha256':plan['sourceScriptSha256']})
    run.finish('write_script',artifact='script-draft.json',format='Spoken opening, context, narrative, takeaway and look-ahead')
    if plan['sourceScriptSha256']!=evidence['sourceScriptSha256']:raise ValueError('Source revision requires a new accuracy edit')
    full=' '.join(scripts.values())
    if not 35<=len(full.split())<=420:raise ValueError('Broadcast script length needs an editorial edit')
    if re.search(r'ignore previous|system prompt|guaranteed to|certain to',full,re.I):raise ValueError('Script contains an instruction or unsupported certainty')
    if not plan.get('why') or not plan.get('summary') or not plan.get('lookAhead'):raise ValueError('Incomplete broadcast structure')
    checks={'sourceBinding':'passed','broadcastStructure':'passed','voice':'calm, attributed, factual; look-ahead framed as a question or milestone','accuracyBasis':'Existing source-bound editorial plan, with source-revision and structure checks. Not independent fact verification.','scriptSha256':digest(full)}
    pipeline.write_json(run.folder/'script-edited.json',{'scripts':scripts,'review':checks})
    run.finish('edit_script',artifact='script-edited.json',**checks)
    return scripts

def cue_time(cue,captions,chapter,word_timings=None):
    """Locate a unique spoken cue; prefer model duration-aligned word boundaries."""
    normalize=lambda text: re.findall(r"[a-z0-9]+",text.lower())
    phrases=[c for c in (word_timings or captions) if chapter['start']<=c['start']<chapter['end']]
    words=[];times=[]
    for phrase in phrases:
        tokens=normalize(phrase['text']);words.extend(tokens);times.extend([phrase['start']]*len(tokens))
    target=normalize(cue)
    if not target:raise ValueError('Empty visual cue')
    matches=[i for i in range(len(words)-len(target)+1) if words[i:i+len(target)]==target]
    if len(matches)!=1:raise ValueError('Visual cue must match exactly one spoken phrase')
    return times[matches[0]]

def timed_reveals(reveals,captions,chapter,word_timings=None):
    values=[{'start':cue_time(r['cue'],captions,chapter,word_timings),'reveal':i} for i,r in enumerate(reveals)]
    if any(b['start']<a['start'] for a,b in zip(values,values[1:])):raise ValueError('Visual reveals must follow narration order')
    return values

def timed_beats(beats,captions,chapter,word_timings=None):
    """Bind authored graphics to actual spoken phrases, independently for each voice."""
    if not any(beat.get('cue') for beat in beats):return None
    if not all(beat.get('cue') for beat in beats):raise ValueError('Every explanatory beat needs a narration cue')
    starts=[cue_time(beat['cue'],captions,chapter,word_timings) for beat in beats]
    if any(b<=a for a,b in zip(starts,starts[1:])):raise ValueError('Visual cues must follow narration order')
    # Directed scenes appear at the spoken cue, never before the referenced subject.
    if not any(b.get('kind') for b in beats):starts[0]=chapter['start']
    result=[]
    for i,start in enumerate(starts):
        item={'start':start,'end':starts[i+1] if i+1<len(starts) else chapter['end'],'beat':i}
        if beats[i].get('reveals'):
            item['reveals']=timed_reveals(beats[i]['reveals'],captions,chapter,word_timings)
            if any(r['start']<start or r['start']>=item['end'] for r in item['reveals']):raise ValueError('Reveal falls outside its scene')
        result.append(item)
    return result

def visuals(run,story,plan):
    decisions=[{'phase':'opening','kind':'text-motion','purpose':'Introduce this story and why it matters'}, {'phase':'story','kind':'illustration-video-and-motion-graphics','purpose':'Story-specific illustrative scene and source-bound supporting facts','image':story['image'],'video':story['video'],'beats':plan['beats']}, {'phase':'closing','kind':'text-motion','purpose':'Takeaway and a qualified look-ahead'}]
    directed=plan.get('visualTreatment')=='directed'
    if directed:decisions[1]={'phase':'story','kind':'narration-directed-scenes','purpose':'Distinct, reviewed explanatory scenes revealed at actual spoken phrases','beats':plan['beats']}
    pipeline.write_json(run.folder/'visual-plan.json',{'decision':'mixture','scenes':decisions,'disclosure':'Original explanatory graphics and licensed, credited file photography; photography is a location reference, not evidence of training outcomes.' if directed else 'Conceptual AI illustration; not documentary footage','mapOrChartPolicy':'Only use maps or charts with reviewed coordinates or quantitative evidence; never invent data.'})
    run.finish('plan_visuals',artifact='visual-plan.json',decision='mixture')
    assets=[]
    for key in ('image','video'):
        path=(pipeline.DIST/story[key]).resolve()
        if not path.is_relative_to(pipeline.DIST.resolve()) or not path.is_file():raise ValueError('Missing approved visual asset')
        assets.append({'kind':key,'path':story[key],'sha256':file_hash(path)})
    if story.get('visual',{}).get('storyId')!=story['id']:raise ValueError('Visual belongs to another story')
    for beat in plan['beats']:
        media=beat.get('media')
        if not media:continue
        if not all(media.get(k) for k in ('src','sourceUrl','licenseUrl','license','author','courtesy','sha256','usageApproved')):raise ValueError('Third-party media requires reviewed rights and a courtesy credit')
        path=(pipeline.DIST/media['src']).resolve()
        if not path.is_relative_to(pipeline.DIST.resolve()) or not path.is_file() or file_hash(path)!=media['sha256']:raise ValueError('Third-party media differs from its reviewed asset')
        assets.append({'kind':'licensed-image','path':media['src'],'sha256':media['sha256'],'rights':media})
    graphics={'scenes':decisions,'renderer':'studio.js','rendererSha256':file_hash(pipeline.DIST/'studio.js'),'styleSha256':file_hash(pipeline.DIST/'studio.css'),'rendererDependencies':{p:file_hash(pipeline.DIST/p) for p in ('directed.js','directed.css')},'assets':assets}
    pipeline.write_json(run.folder/'visual-composition.json',graphics)
    run.finish('create_visuals',artifact='visual-composition.json',method='Reuse approved bespoke image and motion video; compose story-specific broadcast graphics',assets=assets)
    return graphics

def create_music(run,settings):
    assets={};rate=24000;seconds=24;count=rate*seconds
    seed=int(run.data['version'][:8],16);base=[130.8128,146.8324,164.8138,174.6141][seed%4]
    for style in ('drift','piano'):
        path=pipeline.DIST/'assets'/'studio'/f"music-{run.data['version']}-{style}.mp3"
        if not path.exists():
            signal=np.zeros(count,dtype=np.float64)
            for index in range(6):
                length=8 if style=='drift' else 5;t=np.arange(rate*length)/rate
                envelope=np.sin(np.pi*t/length)**2 if style=='drift' else (1-np.exp(-t*8))*np.exp(-t*1.3)*np.sin(np.pi*t/length)
                chord=(0,3,7) if (index+seed)%3 else (0,5,9)
                for note in chord:
                    hz=base*2**(note/12);tone=np.sin(2*np.pi*hz*t)+.18*np.sin(2*np.pi*hz*2*t)
                    np.add.at(signal,(np.arange(len(t))+index*rate*4)%count,tone*envelope*.04)
            signal*=.22/max(.22,float(np.max(np.abs(signal))))
            temporary=run.folder/f'music-{style}.wav'
            with wave.open(str(temporary),'wb') as audio:
                audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(rate);audio.writeframes((signal*32767).astype('<i2').tobytes())
            target=run.folder/f'music-{style}.mp3'
            subprocess.run([settings['ffmpeg'],'-v','error','-i',str(temporary),'-c:a','libmp3lame','-b:a','96k','-y',str(target)],check=True,capture_output=True,timeout=30)
            subprocess.run([settings['ffmpeg'],'-v','error','-xerror','-i',str(target),'-f','null','-'],check=True,capture_output=True,timeout=30)
            target.replace(path)
        subprocess.run([settings['ffmpeg'],'-v','error','-xerror','-i',str(path),'-f','null','-'],check=True,capture_output=True,timeout=30)
        assets[style]=path.relative_to(pipeline.DIST).as_posix()
    pipeline.write_json(run.folder/'music.json',{'assets':assets,'composer':'Original deterministic procedural synthesis on CPU','rights':'Original composition; no samples or external music','seed':seed,'duration':seconds,'sha256':{k:file_hash(pipeline.DIST/v) for k,v in assets.items()}})
    run.finish('create_music',artifact='music.json',method='Original story-seeded ambient and gentle-key beds; viewer can choose silence')
    return assets

def publish_record(story):
    folder=pipeline.WORK/'runs'/'programmes'/story['programmeVersion'];path=folder/'production.json'
    if not path.exists():return
    data=json.loads(path.read_text(encoding='utf-8'))
    if [s['stage'] for s in data['stages']]!=STAGES[:-1]:return
    edition=json.loads((pipeline.DIST/'programmes.json').read_text(encoding='utf-8'))
    if not any(s['id']==story['id'] and s.get('programmeVersion')==story['programmeVersion'] for s in edition['stories']):raise ValueError('Package is not in the published edition')
    data['stages'].append({'stage':'publish','completedAt':pipeline.stamp(),'artifact':'dist/programmes.json','entryPolicy':'Join the viewer playlist at the next story boundary'})
    data['state']='published';pipeline.write_json(path,data)


def cache_valid(folder,story):
    """Never publish a cached package whose composition or media changed."""
    try:
        record=json.loads((folder/'production.json').read_text(encoding='utf-8'))
        if record['state']=='held':return False
        stages=[s['stage'] for s in record['stages']]
        if stages not in (STAGES,STAGES[:-1]):return False
        music=json.loads((folder/'music.json').read_text(encoding='utf-8'))
        composition=json.loads((folder/'visual-composition.json').read_text(encoding='utf-8'))
        checks=[(v['audio'],v['sha256']) for v in story['voices'].values()]
        checks += [(path,music['sha256'][style]) for style,path in music['assets'].items()]
        checks += [(v['path'],v['sha256']) for v in composition['assets']]
        checks += [('studio.js',composition['rendererSha256']),('studio.css',composition['styleSha256'])]
        checks += list(composition.get('rendererDependencies',{}).items())
        for value,expected in checks:
            path=(pipeline.DIST/value).resolve()
            if not path.is_relative_to(pipeline.DIST.resolve()) or file_hash(path)!=expected:return False
        return True
    except (OSError,ValueError,KeyError,TypeError):return False
