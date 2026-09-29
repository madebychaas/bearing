"""Local personal headline playback: source titles, original motion typography, Piper.

This lane reads only public headline metadata. It does not lift article excerpts,
invent a summary, or relax the illustrated channel's script/artwork review gates.
Every source revision gets immutable media; only fully decoded pairs are published.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pipeline
import editorial

ROOT = pipeline.ROOT
DIST = pipeline.DIST
WORK = pipeline.WORK
RENDER_VERSION = 'headline-film-v1-bearing'
PALETTES = {'world':(176,200,224),'business':(197,208,174),'technology':(167,202,218),
            'culture':(214,181,166),'nature':(166,204,177),'space':(179,179,223),
            'health':(173,207,201),'sport':(214,196,151),'local':(212,183,194)}

def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def eligible(items, now=None):
    now = now or datetime.now(timezone.utc)
    result = []
    seen = set()
    for item in items:
        try:
            value = item['publishedTime']
            if not isinstance(value,str) or 'T' not in value:continue
            published = datetime.fromisoformat(value.replace('Z','+00:00'))
            if published.tzinfo is None or not now-timedelta(hours=24) <= published <= now:continue
            pipeline.validate_url(item['source']['url'])
            title = item['title']
            if item['topic'] not in PALETTES or not isinstance(title,str) or not 15 <= len(title) <= 180:continue
            if len(title.split()) < 4 or len(title.split()) > 40 or re.search(r'[<>\x00-\x1f]',title):continue
            if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',item['id']):continue
            if item['source']['url'] in seen:continue
            seen.add(item['source']['url']);result.append(item)
        except (KeyError,TypeError,ValueError):continue
    return sorted(result,key=lambda item:item['publishedTime'],reverse=True)

def production_order(items, maximum=32):
    if any(item.get("editorial") for item in items):return editorial.rank(items,maximum)
    # Legacy records without an editorial assessment retain topic balancing.
    groups = {}
    for item in items:groups.setdefault(item['topic'],[]).append(item)
    result=[]
    while groups and len(result)<maximum:
        for topic in list(groups):
            result.append(groups[topic].pop(0))
            if not groups[topic]:del groups[topic]
            if len(result)>=maximum:break
    return result

def script_for(item):
    title = item['title'].strip()
    return f"A headline from {item['source']['name']}. {title}{'' if title[-1] in '.?!' else '.'}"

def media_key(item):
    # Source, headline and publication time are visible and spoken evidence.
    return digest(json.dumps([RENDER_VERSION,item['id'],item['title'],item['topic'],item['source'],item['publishedTime']],sort_keys=True))[:20]

def font(size, weight='regular'):
    names = {'regular':'segoeui.ttf','light':'segoeuil.ttf','bold':'seguisb.ttf'}
    path = Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/names[weight]
    if not path.exists():raise RuntimeError('Install the configured editorial font before rendering')
    return ImageFont.truetype(str(path),size)

def wrap(draw,text,face,width):
    lines=[];line=''
    for word in text.split():
        candidate=f'{line} {word}'.strip()
        if draw.textlength(candidate,font=face)>width and line:lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    return lines

def render_card(item,path):
    """A factual typographic graphic, not an illustration or purported news image."""
    w,h=1280,720;accent=PALETTES[item['topic']]
    image=Image.new('RGB',(w,h));draw=ImageDraw.Draw(image)
    # Quiet, story-seeded tonal field. Geometry has no implied quantitative meaning.
    seed=int(media_key(item)[:6],16);phase=(seed%100)/100
    for y in range(h):
        blend=.014+.023*(y/h)+.006*math.sin(phase+y/h*math.pi)
        draw.line((0,y,w,y),fill=tuple(int(10+c*blend) for c in accent))
    draw.text((70,48),'Bearing',font=font(32,'bold'),fill=(231,237,230))
    draw.text((950,61),'HEADLINE BRIEFING',font=font(16),fill=(151,169,169))
    draw.line((70,115,1210,115),fill=(51,64,67),width=1)
    label=item.get('topicLabel',pipeline.TOPICS[item['topic']]).upper()
    draw.rectangle((70,158,76,178),fill=accent)
    draw.text((92,153),label,font=font(20),fill=accent)
    for size in range(66,39,-2):
        face=font(size,'light');lines=wrap(draw,item['title'],face,1120)
        if len(lines)<=4:break
    if len(lines)>4 or any(draw.textlength(line,font=face)>1120 for line in lines):
        raise ValueError('Headline does not fit the editorial frame')
    y=218+(4-len(lines))*12
    for line in lines:draw.text((68,y),line,font=face,fill=(239,241,233));y+=size*1.22
    draw.line((70,577,1210,577),fill=(51,64,67),width=1)
    draw.text((70,603),item['source']['name'],font=font(24),fill=accent)
    when=datetime.fromisoformat(item['publishedTime'].replace('Z','+00:00')).astimezone(timezone.utc)
    stamp=when.strftime('%d %b %Y  /  %H:%M UTC')
    draw.text((1210-draw.textlength(stamp,font=font(20)),608),stamp,font=font(20),fill=(155,171,169))
    draw.text((70,661),'PUBLISHER HEADLINE  /  AI VOICE + MOTION GRAPHIC',font=font(15),fill=(120,139,138))
    image.save(path)

def verified_existing(item):
    path=WORK/'runs'/'latest-video'/media_key(item)/'segment.json'
    if not path.exists():return None
    segment=read_json(path,{})
    try:
        for key,hash_key in [('image','imageSha256')]:
            p=DIST/segment[key]
            if hashlib.sha256(p.read_bytes()).hexdigest()!=segment[hash_key]:return None
        for voice in ('warm','measured'):
            track=segment['voices'][voice];p=DIST/track['video']
            if not track['fullDecodePassed'] or hashlib.sha256(p.read_bytes()).hexdigest()!=track['sha256']:return None
    except (KeyError,OSError):return None
    return {**segment,'coverage':item.get('coverage'),'editorial':item.get('editorial') or editorial.assess(item),'sourceAvailable':item.get('sourceAvailable',True)}

def build(item,settings):
    from speech import synthesize
    key=media_key(item);run=WORK/'runs'/'latest-video'/key;run.mkdir(parents=True,exist_ok=True)
    assets=DIST/'assets'/'latest';assets.mkdir(parents=True,exist_ok=True)
    image=assets/f'{key}.png';render_card(item,image)
    script=script_for(item);voices={};ffmpeg=settings['ffmpeg']
    for voice in ('warm','measured'):
        audio=run/f'{voice}.mp3';provenance=audio.with_suffix('.provenance.json')
        meta=read_json(provenance,{})
        if not (audio.exists() and meta.get('scriptSha256')==digest(script) and meta.get('sha256')==hashlib.sha256(audio.read_bytes()).hexdigest()):
            # A partial earlier attempt is retained; use a fresh attempt filename.
            if audio.exists():audio=run/f'{voice}-{datetime.now(timezone.utc).strftime("%H%M%S%f")}.mp3'
            meta=synthesize(script,voice,audio,settings['modelDir'])
        if not 3<=meta['duration']<=40:raise ValueError('Headline narration duration is outside the production limit')
        duration=meta['duration']+1.5;frames=math.ceil(duration*24)
        target=assets/f'{key}-{voice}.mp4';temp=run/f'{voice}-render.mp4'
        motion=f"scale=1920:1080,zoompan=z='1+0.005*on/{frames}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1280x720:fps=24,fade=t=in:st=0:d=0.3"
        subprocess.run([ffmpeg,'-hide_banner','-nostdin','-v','error','-loop','1','-framerate','24','-i',str(image),'-i',str(audio),'-vf',motion,'-af','apad=pad_dur=1.5','-t',str(duration),'-c:v','libx264','-preset','veryfast','-crf','23','-threads','2','-filter_threads','1','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart','-y',str(temp)],check=True,capture_output=True,timeout=120)
        subprocess.run([ffmpeg,'-hide_banner','-nostdin','-v','error','-xerror','-i',str(temp),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True,capture_output=True,timeout=60)
        if temp.stat().st_size<5000:raise ValueError('Incomplete video output')
        os.replace(temp,target)
        voices[voice]={'video':target.relative_to(DIST).as_posix(),'duration':duration,'captions':meta['captions'],'provider':meta['provider'],'scriptSha256':meta['scriptSha256'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'fullDecodePassed':True}
    segment={**{k:item[k] for k in ('id','topic','topicLabel','title','publishedTime','source','version')},'coverage':item.get('coverage'),'editorial':item.get('editorial') or editorial.assess(item),'mediaVersion':key,'status':'ready','format':'headline-video','builtAt':pipeline.stamp(),'script':script,'image':image.relative_to(DIST).as_posix(),'imageSha256':hashlib.sha256(image.read_bytes()).hexdigest(),'voices':voices,'sourceAvailable':item.get('sourceAvailable',True),'visualDisclosure':'Original animated headline graphic. AI voice reads the attributed publisher headline; this is not live footage or an independently verified summary.'}
    pipeline.write_json(run/'segment.json',segment);return segment

def produce(limit=8):
    settings=read_json(WORK/'runtime.json',{})
    for key,env in [('modelDir','CURRENT_PIPER_MODEL_DIR'),('ffmpeg','CURRENT_FFMPEG')]:
        if settings.get(key):os.environ[env]=settings[key]
    reports=read_json(DIST/'reporting.json',{'items':[]})
    items=production_order(eligible(reports['items']));segments=[];errors=[];generated=0
    for item in items:
        segment=verified_existing(item)
        if not segment and generated<limit:
            try:segment=build(item,settings);generated+=1;print(json.dumps({'produced':item['id'],'topic':item['topic']}),flush=True)
            except Exception as exc:
                generated+=1;errors.append({'id':item['id'],'error':str(exc)[:300]})
        if segment:segments.append(segment)
    # Drop changed/stale source versions immediately. A failed render cannot revive them.
    segments.sort(key=lambda s:s['publishedTime'],reverse=True)
    previous=read_json(DIST/'latest-edition.json',{})
    version=digest(json.dumps([(s['id'],s['mediaVersion'],s['sourceAvailable'],s.get('editorial'),s.get('coverage')) for s in segments]))
    if previous.get('version')!=version:
        if previous:pipeline.write_json(WORK/'runs'/'latest-video-editions'/f"{previous['version']}.json",previous)
        pipeline.write_json(DIST/'latest-edition.json',{'version':version,'builtAt':pipeline.stamp(),'format':'headline-video','stories':segments})
    result={'checkedAt':pipeline.stamp(),'ready':len(segments),'target':len(items),'attempted':generated,'errors':errors}
    pipeline.write_json(WORK/'runs'/'latest-video-status.json',result)
    print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=8);args=parser.parse_args()
    with pipeline.production_lock():produce(max(1,min(args.limit,32)))
