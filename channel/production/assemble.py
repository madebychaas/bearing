"""Import retained narration assets, validate them, and publish an edition."""
import argparse, json, shutil
from pathlib import Path
from pipeline import ROOT, DIST, publish

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--media-dir',type=Path,required=True);args=parser.parse_args()
    edition=json.loads((ROOT/'production'/'edition-source.json').read_text(encoding='utf-8'))
    for story in edition['stories']:
        story['video']=f'assets/{story["topic"]}-motion.mp4';story['voices']={}
        for voice in ['warm','measured']:
            stem=f'{story["topic"]}-{voice}'
            metadata=json.loads((args.media_dir/f'{stem}.provenance.json').read_text(encoding='utf-8'))
            shutil.copy2(args.media_dir/f'{stem}.mp3',DIST/'assets'/f'{stem}.mp3')
            story['voices'][voice]={key:metadata[key] for key in ['duration','captions','provider','voice','scriptSha256','modelSha256','captionTiming','sha256']}
            story['voices'][voice]['audio']=f'assets/{stem}.mp3'
    publish(edition)

if __name__=='__main__':main()
