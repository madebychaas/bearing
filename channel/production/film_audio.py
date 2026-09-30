"""Finished-film audio: intact speech, bounded silence edits, original dry score.

No downloads, samples, voice-model changes or sentence-speed changes occur here.
The procedural score is sparse accompaniment, with no melody or swelling pad.
"""
import copy
import math
import re

import numpy as np

RATE=24000


def compact_silence(samples,metadata,policy,rate=RATE):
    """Remove only quiet PCM inside gaps between model-timed spoken words."""
    output=np.asarray(samples).copy();meta=copy.deepcopy(metadata)
    if not policy:return output,meta
    sentence=float(policy.get('minimumSentenceGap',.20));phrase=float(policy.get('minimumPhraseGap',.12))
    if not .16<=sentence<=.4 or not .1<=phrase<=.25:raise ValueError('Keep natural sentence and phrase breathing room')
    edits=[];words=meta.get('wordTimings',[])
    for previous,following in zip(words,words[1:]):
        gap=following['start']-previous['end'];minimum=sentence if re.search(r'[.!?][\"\u201d\u2019]?$',previous['text']) else phrase
        removable=min(.35,gap-minimum)
        if removable<.025:continue
        # Forty milliseconds of untouched sound on each side protects soft
        # consonants and aspiration beyond the model's nominal word markers.
        left=math.ceil((previous['end']+.04)*rate);right=math.floor((following['start']-.04)*rate)
        if right<=left:continue
        quiet=np.abs(output[left:right])<=.002
        edges=np.diff(np.r_[False,quiet,False].astype(np.int8));starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)
        if not len(starts):continue
        best=int(np.argmax(ends-starts));a=left+int(starts[best]);b=left+int(ends[best])
        count=min(round(removable*rate),b-a-round(.02*rate))
        if count<round(.025*rate):continue
        first=a+(b-a-count)//2;last=first+count
        edits.append({'startSample':first,'endSample':last,'after':previous['text'],'before':following['text'],'removedSeconds':round(count/rate,5),'gapBefore':round(gap,5),'gapAfter':round(gap-count/rate,5),'quietPeak':round(float(np.max(np.abs(output[first:last]))),7)})
    for edit in reversed(edits):
        output=np.concatenate((output[:edit['startSample']],output[edit['endSample']:]))
    def shifted(value):
        sample=value*rate
        return round((sample-sum(max(0,min(sample,e['endSample'])-e['startSample']) for e in edits))/rate,5)
    for field in ('captions','wordTimings'):
        for item in meta.get(field,[]):item['start']=shifted(item['start']);item['end']=shifted(item['end'])
    meta['duration']=len(output)/rate
    meta['silenceEdits']=[{key:value for key,value in edit.items() if key not in ('startSample','endSample')} for edit in edits]
    meta['silencePolicy']={'minimumSentenceGap':sentence,'minimumPhraseGap':phrase,'speechGuardSeconds':.04,'maximumRemovalPerGap':.35,'quietPeakLimit':.002,'voiceRateUnchanged':True}
    return output,meta


def editorial_score(style,seconds,rate=RATE):
    """Original restrained pulse / muted-key variants; never borrowed music."""
    count=round(seconds*rate);signal=np.zeros(count,dtype=np.float64)
    def place(start,length,hz,level,keys=False):
        offset=round(start*rate);length=min(round(length*rate),count-offset)
        if length<=0:return
        time=np.arange(length)/rate
        # Fast, rounded attack and short dry release. No bell harmonics,
        # sentimental progression, riser, or long ambient resonance.
        envelope=(1-np.exp(-time/ .003))*np.exp(-time/(.105 if keys else .065))
        envelope*=np.clip((length/rate-time)/.02,0,1)
        tone=np.sin(2*np.pi*hz*time)+(.16 if keys else .06)*np.sin(2*np.pi*hz*2*time)
        if keys:tone+=.22*np.sin(2*np.pi*hz*1.5*time)
        signal[offset:offset+length]+=tone*envelope*level
    if style in ('signature','handoff','bridge'):
        place(0,.23,110,.075,True)
        if style=='bridge':place(.68,.25,82.4069,.025)
    else:
        # One finite composition spans the film, rather than a short repeated
        # loop. Phrase starts get modest weight; most of the speech is clear.
        for index,start in enumerate(np.arange(.4,max(.4,seconds-.4),.8)):
            if index%8 in (3,6,7):continue
            level=(.27 if style=='piano' else .24)*(1 if index%8==0 else .55)
            place(float(start),.34 if style=='piano' else .26,130.8128 if style=='piano' else 82.4069,level,style=='piano')
        signal*=np.clip((seconds-np.arange(count)/rate)/.25,0,1)
    return signal


def mix(narration,track,bed,signature,handoff,rate=RATE):
    """Keep narration at unity gain, including its first phoneme."""
    duration=len(narration)/rate;frames=np.arange(math.ceil(duration*60)+1)/60
    ease=lambda value:np.clip(value,0,1)**2*(3-2*np.clip(value,0,1))
    speech=np.zeros(len(frames),dtype=bool)
    for caption in track['captions']:speech|=(frames>=caption['start']-.2)&(frames<caption['end']+.25)
    desired=.12*np.where(speech,.55,.95)*ease(frames/.035)*ease((duration-frames)/.5)
    gain=np.zeros(len(frames))
    for index in range(1,len(frames)):
        tau=.09 if desired[index]<gain[index-1] else .35
        gain[index]=gain[index-1]+(desired[index]-gain[index-1])*(1-math.exp(-1/60/tau))
    if len(bed)<len(narration):raise ValueError('A finite score must cover the complete film without looping')
    accompaniment=bed[:len(narration)]*np.interp(np.arange(len(narration))/rate,frames,gain)
    for source,start in ((signature,0),(handoff,max(0,track['captions'][-1]['end']-.3))):
        offset=round(start*rate);length=min(len(source),len(narration)-offset)
        if length>0:accompaniment[offset:offset+length]+=source[:length]*.62
    if float(np.max(np.abs(narration)))>.94:raise ValueError('Narration peak needs review; do not silently fade or limit the voice')
    score_gain=1.0
    while np.max(np.abs(narration+accompaniment*score_gain))>.94:score_gain*=.9
    accompaniment*=score_gain;result=narration+accompaniment
    first=track['wordTimings'][0];left=round(first['start']*rate);right=round(first['end']*rate)
    db=lambda value:round(float(20*np.log10(max(1e-9,np.sqrt(np.mean(value**2))))),3)
    evidence={'profile':'restrained-editorial-v2','music':'drift','musicVolume':.12,'dialogueDuck':.55,'effectsGain':.62,'voiceGain':1,'narrationFadeSeconds':0,'scoreHeadroomGain':score_gain,'peak':round(float(np.max(np.abs(result))),6),'firstWord':{'text':first['text'],'start':first['start'],'voiceRmsDbfs':db(narration[left:right]),'accompanimentRmsDbfs':db(accompaniment[left:right])},'rights':'Original dry synthesis; no samples or external music','physicalListeningVerified':False}
    return result,evidence
