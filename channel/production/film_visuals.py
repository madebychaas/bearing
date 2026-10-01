"""Original, narration-timed editorial graphics rendered into a self-contained film.

The scene changes are authored in the reviewed packet. All numeric labels are
literal supplied data; bar geometry starts at zero. No remote assets, random
camera movement, or generated documentary imagery enter this renderer.
"""
from __future__ import annotations

import hashlib
import math
import os
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT, FPS = 1920, 1080, 30
SCALE = WIDTH / 1280
TRANSITION_SECONDS = 1.5
IVORY = (244, 242, 233)
INK = (24, 43, 45)
TEAL = (56, 118, 108)
MUTED = (107, 122, 116)
GOLD = (174, 153, 113)


def ease(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def reveal_progress(time, start, duration=.7):
    return 0.0 if time < start else ease((time - start) / duration)


def _mix(first, second, progress):
    return tuple(round(a + (b - a) * progress) for a, b in zip(first, second))


@lru_cache(maxsize=64)
def _font(size, weight='regular'):
    windows = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    filename = {'light': 'segoeuil.ttf', 'regular': 'segoeui.ttf', 'bold': 'seguisb.ttf'}[weight]
    candidates = [windows / filename, windows / ('arialbd.ttf' if weight == 'bold' else 'arial.ttf'),
                  Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), round(size * SCALE))
    raise RuntimeError('Install a readable editorial sans-serif font before rendering')


def _point(x, y):
    return round(x * SCALE), round(y * SCALE)


def _line(draw, coords, fill, width=1):
    draw.line([_point(*p) for p in coords], fill=fill, width=max(1, round(width * SCALE)))


def _circle(draw, x, y, radius, fill, outline=None, width=1):
    draw.ellipse((*_point(x-radius, y-radius), *_point(x+radius, y+radius)), fill=fill,
                 outline=outline, width=max(1, round(width * SCALE)))


def _text(draw, x, y, text, size, fill, weight='regular', anchor=None):
    draw.text(_point(x, y), str(text), font=_font(size, weight), fill=fill, anchor=anchor,
              stroke_width=0)


def _wrap(draw, text, size, width, weight='regular'):
    lines = []
    for paragraph in str(text).split('\n'):
        line = ''
        for word in paragraph.split():
            proposed = (line + ' ' + word).strip()
            if line and draw.textlength(proposed, font=_font(size, weight)) > width * SCALE:
                lines.append(line); line = word
            else:
                line = proposed
        lines.append(line)
    return lines


def _paragraph(draw, x, y, text, size, width, fill, weight='regular', max_lines=3):
    while size > 20:
        lines = _wrap(draw, text, size, width, weight)
        if len(lines) <= max_lines:
            break
        size -= 2
    if len(lines) > max_lines:
        raise ValueError('Authored graphic copy exceeds its safe layout')
    for index, line in enumerate(lines):
        _text(draw, x, y + index * size * 1.16, line, size, fill, weight)
    return y + len(lines) * size * 1.16


def _value(number, suffix='%'):
    return f'{float(number):.1f}{suffix}'


def chart_spec(visuals):
    """Validate literal supplied data and preserve a zero-baseline comparison."""
    supplied = visuals.get('comparison', visuals)
    values = [supplied.get('previousValue'), supplied.get('currentValue')]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('Comparison requires two finite, nonnegative reviewed values')
    ceiling = supplied.get('ceiling') or max(1, math.ceil(max(values) + .5))
    if not isinstance(ceiling, (int, float)) or not math.isfinite(ceiling) or ceiling < max(values):
        raise ValueError('Chart ceiling must include both reviewed values')
    if supplied.get('baseline', 0) != 0:
        raise ValueError('Comparative bars require a zero baseline')
    return {'previousValue': values[0], 'currentValue': values[1], 'ceiling': float(ceiling), 'baseline': 0,
            'previousLabel': supplied.get('previousLabel', 'Previous month'),
            'currentLabel': supplied.get('currentLabel', 'Current month'),
            'unit': supplied.get('unit', supplied.get('valueSuffix', '%')),
            'metricLabel': supplied.get('metricLabel', visuals.get('metricLabel', 'PCE price index')),
            'note': supplied.get('note', visuals.get('comparisonLabel', ''))}


def scene_schedule(packet, track):
    """Use produced voice cues, never equal-duration slides or script estimates."""
    duration = float(track['duration'])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('A finished narration duration is required')
    plan = packet['plan']
    chapters = {c['kind']: c for c in track.get('chapters', [])}
    if not all(k in chapters for k in ('opening', 'story', 'closing')):
        raise ValueError('Opening, story and closing chapters are required')
    cues = track.get('visualCues', [])
    if not cues:
        raise ValueError('Narration-aligned visual cues are required')
    result = [{'kind': 'headline', 'start': 0.0, 'end': float(cues[0]['start']),
               'reveals': track.get('openingCues', []), 'definitions': plan.get('openingReveals', []),
               'voiceStart': chapters['opening']['start']}]
    aliases = {'pce_comparison': 'comparison', 'pce_mechanism': 'mechanism',
               'pce_headline': 'headline', 'pce_close': 'close'}
    for cue in cues:
        beat = plan['beats'][cue['beat']]
        kind = aliases.get(beat.get('kind'), beat.get('kind'))
        if kind not in ('headline', 'comparison', 'mechanism', 'service', 'close'):
            raise ValueError(f'No reviewed film layout for scene kind {kind!r}')
        result.append({**cue, 'kind': kind, 'definitions': beat.get('reveals', []), 'label': beat.get('label', ''),
                       'voiceStart': cue['start']})
    closing_cues = track.get('closingCues', [])
    # Carry the evidence under a spoken bridge such as "The next test". The
    # closing question begins when its first authored phrase is actually heard.
    closing = float(closing_cues[0]['start'] if closing_cues else chapters['closing']['start'])
    if not chapters['closing']['start'] <= closing < chapters['closing']['end']:
        raise ValueError('The closing picture cue falls outside the closing chapter')
    definitions = plan.get('closingReveals', [])
    if packet.get('visuals', {}).get('closing', {}).get('kind') == 'default-impact':
        # This story changes editorial tasks inside its closing: first explain
        # that an application is not an outcome, then explain default itself.
        # Use the spoken definition as the cut; do not divide by estimated time.
        required = ('hinge', 'meaning', 'default', 'months', 'credit', 'car', 'home', 'consequence')
        by_role = {definitions[c['reveal']].get('role'): c for c in closing_cues
                   if 0 <= c['reveal'] < len(definitions)}
        if any(role not in by_role for role in required):
            raise ValueError('Default-impact closing requires all eight authored narration cues')
        if any(by_role[b]['start'] <= by_role[a]['start'] for a, b in zip(required, required[1:])):
            raise ValueError('Default-impact cues must follow the reviewed explanation order')
        impact = float(by_role['default']['start'])
        result.append({'kind': 'close', 'start': closing, 'end': impact, 'voiceStart': closing,
                       'reveals': [c for c in closing_cues if c['start'] < impact],
                       'definitions': definitions})
        result.append({'kind': 'default-impact', 'start': impact, 'end': duration, 'voiceStart': impact,
                       'reveals': [c for c in closing_cues if c['start'] >= impact],
                       'definitions': definitions})
    else:
        result.append({'kind': 'close', 'start': closing, 'end': duration, 'voiceStart': closing,
                       'reveals': closing_cues, 'definitions': definitions})
    previous = -1.0
    for scene in result:
        if not 0 <= scene['start'] < scene['end'] <= duration or scene['start'] <= previous:
            raise ValueError('Scene clocks must be ordered and contained in the finished film')
        for reveal in scene.get('reveals', []):
            if not scene['start'] <= reveal['start'] < scene['end']:
                raise ValueError('A reveal falls outside its narrated scene')
        previous = scene['start']
    for first, second in zip(result, result[1:]):
        first['end'] = second['start']
    for scene in result:
        starts = [reveal['start'] for reveal in scene.get('reveals', [])]
        if any(b < a for a, b in zip(starts, starts[1:])):
            raise ValueError('Visual reveals must follow narration order')
        if any(not scene['start'] <= start < scene['end'] for start in starts):
            raise ValueError('A reveal falls outside its narrated scene')
    return result


def role_start(scene, roles, index=0):
    roles = {roles} if isinstance(roles, str) else set(roles)
    definitions = scene.get('definitions', [])
    for cue in scene.get('reveals', []):
        definition = definitions[cue['reveal']] if cue['reveal'] < len(definitions) else {}
        if definition.get('role') in roles:
            return float(cue['start'])
    cues = scene.get('reveals', [])
    return float(cues[index]['start']) if index < len(cues) else float(scene['voiceStart'])


class Film:
    def __init__(self, packet, track):
        self.packet, self.track = packet, track
        self.plan = packet['plan']; self.visuals = packet.get('visuals', {})
        self.scenes = scene_schedule(packet, track)
        self.chart = chart_spec(self.visuals) if any(s['kind']=='comparison' for s in self.scenes) else None
        self.duration = float(track['duration'])
        self.bases = {}

    def base(self, dark):
        if dark not in self.bases:
            background = INK if dark else IVORY
            image = Image.new('RGB', (WIDTH, HEIGHT), background)
            draw = ImageDraw.Draw(image)
            # Native captions stack above the chapter container and transport.
            # Keep meaningful content within the upper 65 percent of the frame.
            _line(draw, [(80, 81), (1200, 81)], _mix(background, IVORY if dark else INK, .17))
            _text(draw, 80, 42, self.visuals.get('credit', 'COURTESY  /  U.S. BUREAU OF ECONOMIC ANALYSIS'), 12,
                  _mix(background, IVORY if dark else INK, .7))
            _text(draw, 1200, 37, 'bearing', 25, IVORY if dark else INK, 'light', anchor='ra')
            self.bases[dark] = image
        return self.bases[dark].copy()

    def scene(self, scene, time):
        kind = scene['kind']; dark = kind in ('headline', 'mechanism')
        image = self.base(dark); draw = ImageDraw.Draw(image)
        background = INK if dark else IVORY; foreground = IVORY if dark else INK
        if kind == 'headline':
            start = role_start(scene, ('headline', 'lead', 'news', 'opening'))
            progress = reveal_progress(time, start, .85)
            _text(draw, 82, 116, self.visuals.get('eyebrow', 'THE PRICE OF EVERYDAY LIFE'), 13, GOLD)
            headline = self.visuals.get('headline', self.plan['title'])
            bottom = _paragraph(draw, 77, 165 + 16*(1-progress), headline, 79, 1030,
                                _mix(background, foreground, progress), 'light', 2)
            subline = self.visuals.get('subline', self.plan.get('why', ''))
            sub_progress = reveal_progress(time, role_start(scene, ('meaning', 'impact', 'subline'), 1), .75)
            _line(draw, [(82, min(bottom+30, 384)), (82+175*progress, min(bottom+30, 384))], GOLD, 2)
            _paragraph(draw, 82, min(bottom+52, 412), subline, 23, 960,
                       _mix(background, foreground, sub_progress*.72), max_lines=2)
        elif kind == 'comparison':
            c = self.chart
            _text(draw, 82, 112, c['metricLabel'].upper(), 14, MUTED)
            _paragraph(draw, 79, 145, self.visuals.get('comparisonTitle', 'The latest reading'), 42, 1050, INK, 'light', 1)
            left, right, top, baseline = 156, 1120, 264, 420
            height = baseline-top
            ticks = max(1, math.ceil(c['ceiling']))
            for tick in range(ticks+1):
                number = c['ceiling']*tick/ticks
                y = baseline-number/c['ceiling']*height
                _line(draw, [(left, y), (right, y)], _mix(IVORY, INK, .22 if tick == 0 else .09))
                _text(draw, left-20, y-11, f'{number:g}', 13, MUTED, anchor='ra')
            # Reading order follows the spoken comparison: current first, then
            # the reference. Color belongs to the meaning, not the column index.
            for i, (x, value, label, roles, bar_color) in enumerate([
                (345, c['currentValue'], c['currentLabel'], ('current', 'august', 'amount', 'inflation'), TEAL),
                (790, c['previousValue'], c['previousLabel'], ('previous', 'july', 'before', 'goal', 'target'), (144, 164, 151))]):
                p = reveal_progress(time, role_start(scene, roles, i), .85)
                color = _mix(IVORY, bar_color, p)
                bar_top = baseline-value/c['ceiling']*height*p
                if p:
                    draw.rounded_rectangle((*_point(x-95, bar_top), *_point(x+95, baseline)),
                                           radius=round(5*SCALE), fill=color)
                    # Cover bottom rounding to keep both bars precisely on zero.
                    draw.rectangle((*_point(x-95, baseline-6), *_point(x+95, baseline)), fill=color)
                _text(draw, x, top-72, _value(value, c['unit']), 59,
                      _mix(IVORY, INK, p), 'light', anchor='ma')
                _text(draw, x, baseline+15, label, 20, _mix(IVORY, INK, p), anchor='ma')
            if c['note']:
                _text(draw, 82, 466, c['note'], 11, MUTED)
        elif kind == 'mechanism':
            m = self.visuals.get('mechanism', {})
            _text(draw, 82, 116, m.get('eyebrow', 'WHAT THE NUMBERS MEAN'), 13, GOLD)
            _paragraph(draw, 78, 151, m.get('title', 'Spending is not the same as buying more.'), 46, 1100,
                       IVORY, 'light', 2)
            steps = m.get('steps', [])
            if not 2 <= len(steps) <= 3:
                raise ValueError('Mechanism needs two or three authored, supported steps')
            xs = [170 + i*(930/(len(steps)-1)) for i in range(len(steps))]
            y = 320
            _line(draw, [(xs[0], y), (xs[-1], y)], _mix(INK, IVORY, .16), 2)
            for i, (x, step) in enumerate(zip(xs, steps)):
                if isinstance(step, str):
                    step = {'label': step}
                p = reveal_progress(time, role_start(scene, (step.get('role', str(i)),), i), .8)
                color = _mix(INK, IVORY, p)
                if i and p:
                    _line(draw, [(xs[i-1], y), (xs[i-1]+(x-xs[i-1])*p, y)], TEAL, 3)
                _circle(draw, x, y, 11+3*p, INK, _mix(INK, GOLD if i == len(steps)-1 else IVORY, p), 2)
                _circle(draw, x, y, 3.5*p, GOLD if i == len(steps)-1 else IVORY)
                if step.get('value') is not None:
                    _text(draw, x, y-106, step['value'], 56, color, 'light', anchor='ma')
                label = step.get('label', '')
                lines = _wrap(draw, label, 22, 280)
                if len(lines) > 2:
                    raise ValueError('Mechanism label needs an editorial trim')
                for j, line in enumerate(lines):
                    _text(draw, x, y+39+j*28, line, 22, color, anchor='ma')
                if step.get('detail'):
                    _text(draw, x, y+111, step['detail'], 14, _mix(INK, IVORY, p*.58), anchor='ma')
            if m.get('note'):
                np = reveal_progress(time, role_start(scene, m.get('noteRole', 'spending'), len(steps)), .8)
                _line(draw, [(82, 450), (82+54*np, 450)], _mix(INK, GOLD, np), 2)
                _text(draw, 157, 433, m['note'], 23, _mix(INK, IVORY, np))
            # Period and aggregate scope belong in the scene eyebrow. A second
            # tiny footer would fall behind the native captions at laptop sizes.
        elif kind == 'service':
            # One explanatory composition holds the two choices while the voice
            # moves into paperwork and tracking. No imitation government UI.
            service = self.visuals.get('service', {})
            options, tools = service.get('options', []), service.get('tools', [])
            if len(options)!=2 or len(tools)!=2:
                raise ValueError('Service graphic needs two reviewed options and two tools')
            _text(draw, 82, 116, service.get('eyebrow', 'THE ONLINE PROCESS'), 13, MUTED)
            _paragraph(draw, 78, 157, service['title'], 43, 1090, INK, 'light', 2)
            for index, option in enumerate(options):
                x=82+index*568
                p=reveal_progress(time,role_start(scene,option['role']),.7)
                border=_mix(IVORY,TEAL,p*.65)
                draw.rounded_rectangle((*_point(x,260),*_point(x+540,359)),radius=round(12*SCALE),outline=border,width=round(1.5*SCALE))
                _text(draw,x+24,283,option['label'],32,_mix(IVORY,INK,p),'light')
                _line(draw,[(x+24,335),(x+24+110*p,335)],_mix(IVORY,TEAL,p),2)
            # A single labeled band avoids implying that each tool belongs to
            # the option directly above it. The packet names the supported scope.
            tools_progress=reveal_progress(time,role_start(scene,tools[0]['role']),.7)
            draw.rounded_rectangle((*_point(82,385),*_point(1190,458)),radius=round(12*SCALE),
                                   outline=_mix(IVORY,TEAL,tools_progress*.35),width=round(SCALE))
            _text(draw,106,404,service.get('toolsLabel','ONLINE TOOLS'),14,_mix(IVORY,MUTED,tools_progress))
            for index, tool in enumerate(tools):
                x=437+index*371
                p=reveal_progress(time,role_start(scene,tool['role']),.7)
                color=_mix(IVORY,TEAL,p)
                _circle(draw,x,430,12,IVORY,color,1.5)
                if index==0:
                    _line(draw,[(x,437),(x,423),(x-4,427)],color,1.5)
                    _line(draw,[(x,423),(x+4,427)],color,1.5)
                else:
                    _line(draw,[(x-5,434),(x-5,430),(x,430),(x,426),(x+5,426)],color,1.5)
                _text(draw,x+25,412,tool['label'],23,_mix(IVORY,INK,p))
        elif kind == 'default-impact':
            impact = self.visuals.get('defaultImpact', {})
            # These labels are reviewed, literal editorial copy. The timeline
            # illustrates the qualified nine-month definition; it is not a
            # fabricated credit score, individual eligibility result or forecast.
            if impact.get('months') != 9 or impact.get('qualifier') != 'Generally, about':
                raise ValueError('Default-impact graphic needs the reviewed qualified nine-month definition')
            p = reveal_progress(time, role_start(scene, 'default'), .9)
            _text(draw, 82, 116, impact.get('eyebrow', 'WHAT DEFAULT CAN MEAN'), 13, MUTED)
            _paragraph(draw, 78, 153, impact.get('title', 'The impact goes beyond the loan.'), 43,
                       1090, _mix(IVORY, INK, p), 'light', 1)

            # A quiet calendar rhythm at left resolves under the spoken period.
            # No consequences appear before their own narration cues.
            months = reveal_progress(time, role_start(scene, 'months'), .7)
            _text(draw, 84, 245, impact['qualifier'], 18, _mix(IVORY, MUTED, months))
            _text(draw, 78, 263, '9', 101, _mix(IVORY, INK, months), 'light')
            _text(draw, 152, 319, 'months', 30, _mix(IVORY, INK, months), 'light')
            _text(draw, 84, 390, 'of missed payments', 21, _mix(IVORY, INK, months))
            for index in range(9):
                tick = reveal_progress(time, role_start(scene, 'months') + index*.045, .55)
                x = 84 + index*29
                draw.rounded_rectangle((*_point(x,432), *_point(x+18,440)), radius=round(4*SCALE),
                                       fill=_mix(IVORY, TEAL, tick*.65))

            credit = reveal_progress(time, role_start(scene, 'credit'), .7)
            _line(draw, [(365, 334), (365+67*credit, 334)], _mix(IVORY, TEAL, credit*.7), 2)
            _circle(draw, 439, 334, 5, IVORY, _mix(IVORY, TEAL, credit), 1.5)
            # Credit is represented by an original report outline, without any
            # lender mark, invented score or pseudo-documentary screenshot.
            card = _mix(IVORY, TEAL, credit*.055)
            draw.rounded_rectangle((*_point(469,244), *_point(769,444)), radius=round(18*SCALE),
                                   fill=card, outline=_mix(IVORY, TEAL, credit*.35), width=round(SCALE))
            icon = _mix(IVORY, TEAL, credit)
            draw.rounded_rectangle((*_point(493,267), *_point(514,295)), radius=round(3*SCALE),
                                   outline=icon, width=round(1.4*SCALE))
            for row in range(3):
                _line(draw, [(499,275+6*row), (508,275+6*row)], icon, 1.3)
            _paragraph(draw, 493, 316, impact.get('creditLabel', 'Can hurt\ncredit'), 39, 260,
                       _mix(IVORY, INK, credit), 'light', 2)

            # Concrete everyday consequences extend in reading order. They
            # remain possibilities: the only outcome line carries "can".
            for index, role in enumerate(('car', 'home')):
                q = reveal_progress(time, role_start(scene, role), .55)
                y = 250 + index*88
                color = _mix(IVORY, TEAL, q)
                _line(draw, [(789, y+29), (812, y+29)], _mix(IVORY, TEAL, q*.7), 1.5)
                draw.rounded_rectangle((*_point(826,y), *_point(1187,y+67)), radius=round(13*SCALE),
                                       fill=_mix(IVORY, TEAL, q*.04),
                                       outline=_mix(IVORY, TEAL, q*.25), width=round(SCALE))
                x = 849
                if role == 'car':
                    _line(draw, [(x,y+39),(x,y+29),(x+6,y+25),(x+12,y+14),
                                 (x+29,y+14),(x+36,y+26),(x+41,y+29),(x+41,y+39)], color, 1.7)
                    _line(draw, [(x+5,y+26),(x+35,y+26)], color, 1.6)
                    _line(draw, [(x+13,y+39),(x+29,y+39)], color, 1.6)
                    _circle(draw,x+8,y+39,5,IVORY,color,1.7)
                    _circle(draw,x+34,y+39,5,IVORY,color,1.7)
                    label = 'Car loan'
                else:
                    _line(draw, [(x+6,y+44),(x+6,y+13),(x+36,y+13),(x+36,y+44)], color, 1.7)
                    _line(draw, [(x+2,y+44),(x+40,y+44)], color, 1.7)
                    for dx in (13,26):
                        for dy in (20,28):
                            _line(draw, [(x+dx,y+dy),(x+dx+4,y+dy)], color, 1.8)
                    _line(draw, [(x+18,y+44),(x+18,y+35),(x+25,y+35),(x+25,y+44)],color,1.6)
                    label = 'Apartment'
                _text(draw,910,y+15,label,28,_mix(IVORY,INK,q),'light')
            consequence = reveal_progress(time, role_start(scene, 'consequence'), .5)
            _text(draw, 838, 430, impact.get('consequenceLabel', 'Can be harder to get'), 21,
                  _mix(IVORY, TEAL, consequence))
        elif kind == 'close':
            close = self.visuals.get('closing', {})
            start = role_start(scene, ('hinge', 'payoff', 'closing', 'target'))
            progress = reveal_progress(time, start, .9)
            _text(draw, 82, 116, close.get('eyebrow', 'THE QUESTION THAT MATTERS'), 13, MUTED)
            _paragraph(draw, 78, 166 + 12*(1-progress), close.get('title', self.visuals.get('closeTitle', self.plan['summary'])),
                       66, 1090, _mix(IVORY, INK, progress), 'light', 3)
            detail = close.get('text', self.visuals.get('closeText', self.plan.get('lookAhead', '')))
            dp = reveal_progress(time, role_start(scene, ('next', 'watch', 'meaning'), 1), .8)
            _paragraph(draw, 84, 400, detail, 25, 950, _mix(IVORY, TEAL, dp), max_lines=2)
            # A route resolves on an open circle: a question, not an invented outcome.
            route = ease((time-start)/1.5)
            if close.get('destination'):
                _text(draw,84,444,close['destination'],19,_mix(IVORY,MUTED,dp))
            else:
                _line(draw, [(84, 455), (84+960*route, 455)], _mix(IVORY, TEAL, .5), 2)
                if route:
                    _circle(draw, 84+960*route, 455, 7, IVORY, TEAL, 2)
        return image

    def frame(self, time):
        time = min(max(float(time), 0), self.duration-1/FPS)
        index = max(i for i, scene in enumerate(self.scenes) if scene['start'] <= time)
        scene = self.scenes[index]
        current = self.scene(scene, time)
        if index and time < scene['start']+TRANSITION_SECONDS:
            previous = self.scene(self.scenes[index-1], scene['start']-1/FPS)
            current = Image.blend(previous, current, ease((time-scene['start'])/TRANSITION_SECONDS))
        return current

    def contact_sheet(self, path):
        sheet = Image.new('RGB', (1280, 400*math.ceil(len(self.scenes)/2)), IVORY)
        draw = ImageDraw.Draw(sheet)
        samples = []
        for index, scene in enumerate(self.scenes):
            time = min(scene['end']-.15, max(scene['start']+TRANSITION_SECONDS, scene['end']-.65))
            x, y = (index % 2)*640, (index//2)*400
            sheet.paste(self.frame(time).resize((640, 360), Image.Resampling.LANCZOS), (x, y))
            draw.text((x+16, y+371), f"{scene['kind']} / {time:.2f}s", fill=INK,
                      font=ImageFont.truetype(_font(12).path, 16))
            samples.append({'kind': scene['kind'], 'time': round(time, 3)})
        sheet.save(path)
        return samples


def render(packet, track, output_mp4: Path, poster_png: Path, ffmpeg: str):
    """Render silent H.264 and poster; leave delivery mixing to produce_film."""
    movie = Film(packet, track)
    output_mp4, poster_png = Path(output_mp4), Path(poster_png)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    poster_png.parent.mkdir(parents=True, exist_ok=True)
    poster_time = min(movie.scenes[0]['end']-.1, max(1.6, movie.scenes[0]['end']-.6))
    movie.frame(poster_time).save(poster_png)
    contact = poster_png.with_name(poster_png.stem+'-contact.png')
    sample_frames = movie.contact_sheet(contact)
    frames = round(movie.duration*FPS)
    if abs(frames/FPS-movie.duration) > .001:
        raise ValueError('Film duration must be aligned to the delivery frame clock')
    command = [str(ffmpeg), '-hide_banner', '-loglevel', 'error', '-nostdin', '-f', 'rawvideo',
               '-pix_fmt', 'rgb24', '-s', f'{WIDTH}x{HEIGHT}', '-r', str(FPS), '-i', 'pipe:0',
               '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-threads', '4',
               '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-y', str(output_mp4)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for index in range(frames):
            process.stdin.write(movie.frame(index/FPS).tobytes())
        process.stdin.close()
        stderr = process.stderr.read().decode('utf-8', errors='replace')
        if process.wait(timeout=120):
            raise RuntimeError(f'Film encode failed: {stderr[-1500:]}')
    except BaseException:
        process.kill(); process.wait()
        raise
    return {'renderer': 'film_visuals.py', 'width': WIDTH, 'height': HEIGHT, 'fps': FPS,
            'duration': movie.duration, 'frames': frames, 'audio': False,
            'transitionSeconds': TRANSITION_SECONDS, 'cameraMotion': 'none',
            'captionSafeArea': 'Bottom 35 percent reserved for native captions, chapters and transport',
            'chart': movie.chart, 'scenes': movie.scenes, 'contactSheet': str(contact),
            'sampleFrames': sample_frames, 'videoSha256': hashlib.sha256(output_mp4.read_bytes()).hexdigest(),
            'posterSha256': hashlib.sha256(poster_png.read_bytes()).hexdigest(),
            'thirdPartyImages': [], 'attribution': packet.get('visuals',{}).get('credit','Data: U.S. Bureau of Economic Analysis')+'; original Bearing graphics'}
