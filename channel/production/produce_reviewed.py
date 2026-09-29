"""Produce an explicitly reviewed source file through the normal media gates."""
import argparse, asyncio, json, os
from datetime import datetime, timezone
from pathlib import Path
import pipeline

async def produce(path):
    payload=json.loads(path.read_text(encoding='utf-8'))
    edition=json.loads((pipeline.DIST/'edition.json').read_text(encoding='utf-8'))
    known={s['id'] for s in edition['stories']}
    run=pipeline.WORK/'runs'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
    completed=[]
    for story in payload['stories']:
        if story['id'] in known:continue
        if story.get('reviewStatus')!='verified' or not story.get('reviewedAt'):raise ValueError('Explicit source review required')
        pipeline.attach_visual(story)
        story['voices']={}
        for voice in pipeline.VOICES:story['voices'][voice]=await pipeline.narrate(story,voice,run)
        pipeline.check_story(story);completed.append(story)
    if completed:pipeline.publish({'edition':datetime.now(timezone.utc).date().isoformat(),'stories':edition['stories']+completed})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);args=parser.parse_args()
    settings=json.loads((pipeline.WORK/'runtime.json').read_text(encoding='utf-8'))
    os.environ['CURRENT_PIPER_MODEL_DIR']=settings['modelDir'];os.environ['CURRENT_FFMPEG']=settings['ffmpeg']
    with pipeline.production_lock():asyncio.run(produce(args.input))
