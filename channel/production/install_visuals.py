"""Install an inspected image-generation manifest and compose gentle story loops.

This is an explicit production step, not an unattended image generator. The
manifest must contain storyId, filename, path, prompt, disclosure, inspection,
and hash.value for every asset. Existing files are never overwritten.
"""
import argparse, hashlib, json, os, re, shutil, subprocess
from pathlib import Path
import pipeline

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def install(manifest_path):
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    edition=json.loads((pipeline.DIST/'edition.json').read_text(encoding='utf-8'))
    stories={s['id']:s for s in edition['stories']}
    candidates=pipeline.WORK/'candidates'/'latest.json'
    if candidates.exists():
        for story in json.loads(candidates.read_text(encoding='utf-8'))['candidates']:stories.setdefault(story['id'],story)
    registry=pipeline.visual_registry()
    for item in manifest['assets']:
        if not item.get('inspection') or not item.get('prompt'):raise ValueError('Visual inspection and prompt must be recorded')
        story=stories[item['storyId']];name=item['filename']
        if not re.fullmatch(r'[a-z0-9-]+\.png',name):raise ValueError('Use a versioned PNG asset filename')
        source=Path(item['path']);image=pipeline.asset('assets/'+name)
        if digest(source)!=item['hash']['value'].lower():raise ValueError('Generated original hash mismatch')
        if image.exists() and digest(image)!=digest(source):raise ValueError('Use a new filename to preserve prior artwork')
        if not image.exists():shutil.copy2(source,image)
        video=image.with_name(image.stem+'-motion.mp4')
        if not video.exists():
            temporary=video.with_name(video.stem+'.rendering.mp4')
            command=[pipeline.ffmpeg(),'-v','error','-y','-loop','1','-i',str(image),'-vf',"scale=1920:-2,zoompan=z='1.01-0.01*cos(2*PI*on/287)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=288:s=1280x720:fps=24",'-frames:v','288','-c:v','libx264','-threads','2','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(temporary)]
            subprocess.run(command,check=True,timeout=180)
            pipeline.decode(temporary);os.replace(temporary,video)
        pipeline.decode(video)
        registry[story['id']]={'scope':'story','storyId':story['id'],'scriptSha256':pipeline.script_hash(story),'image':'assets/'+image.name,'video':'assets/'+video.name,'imageSha256':digest(image),'videoSha256':digest(video),'alt':item.get('alt',item['inspection'].removeprefix('Visually inspected: ')),'disclosure':item['disclosure'],'reviewedAt':pipeline.stamp(),'reviewedBy':'Codex visual inspection','generator':manifest['generator'],'prompt':item['prompt'],'inspection':item['inspection'],'motion':'12 second seamless cosine zoom, 1.00 to 1.02, 24 fps, CPU-composed'}
        print(f'Installed bespoke visual: {story["id"]}',flush=True)
    pipeline.write_json(pipeline.WORK/'visuals.json',{'schemaVersion':1,'visuals':registry})
    # Publication is separate so an incomplete visual batch cannot replace an edition.

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True);args=parser.parse_args()
    settings=json.loads((pipeline.WORK/'runtime.json').read_text(encoding='utf-8'));os.environ['CURRENT_FFMPEG']=settings['ffmpeg']
    with pipeline.production_lock():install(args.manifest)
