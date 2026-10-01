"""Produce a personal cast from exact approved native editorial handoffs.

This adapter does not claim autonomous reporting, direction or image generation.
Those services must supply a reviewed handoff before this existing film machinery
can run. Personal outputs never replace the channel's public film manifest.
"""
from __future__ import annotations

import copy


class NeedsProductionConnection(RuntimeError):
    needs_attention = True


def capabilities(root):
    return {
        'generationReady': False,
        'summary': 'Automatic writing and original imagery need a generation connection. Reviewed stories can already be produced.',
        'mode': 'reviewed-production',
    }


STAGE_AFTER = {
    'source': ('writing', 'Preparing the story'),
    'write_script': ('editing', 'Checking the script'),
    'edit_script': ('voicing', 'Recording the narration'),
    'tts': ('directing', 'Matching the picture to the voice'),
    'plan_visuals': ('creating_visuals', 'Producing the picture'),
    'create_visuals': ('scoring', 'Shaping the sound'),
    'create_music': ('assembling', 'Bringing the story together'),
    'assemble': ('checking', 'Checking the finished story'),
}


def check_evidence(chosen, record):
    """A shared event ID alone cannot bind a new report to an old script."""
    from selection import bound_content
    approved = {item['id']: item for item in record.get('evidence', [])
                if item.get('origin') == 'intake'}
    if not chosen.get('evidence'):
        raise NeedsProductionConnection('The selected reporting needs a fresh editorial review before production.')
    for report in chosen['evidence']:
        source = {'id': report['id'], 'url': report['url'], 'headline': report['title'],
                  'excerpt': report.get('excerpt', ''), 'publishedTime': report.get('publishedAt')}
        previous = approved.get(report['id'])
        if not previous or bound_content([source]) != bound_content([previous]):
            raise NeedsProductionConnection('This story has newer reporting than its approved script. Review that reporting before making the newscast.')


def validate_ready(job, result, guard, root, *, handoff=None):
    """Repeat exact authority checks after costly media verification."""
    if handoff is None:
        raise NeedsProductionConnection('Production review is unavailable. Your finished media has been preserved.')
    guard()
    for chosen, story in zip(job['stories'], result['stories']):
        lineage = story['production']['selection']
        record = handoff._guard(chosen['id'], 'live', lineage['approval']['id'])
        check_evidence(chosen, record)
        current = handoff._lineage(record)
        if any(current.get(key) != lineage.get(key) for key in
               ('selectionId', 'eventId', 'mode', 'sourceRevision', 'scriptRevision', 'voiceRevision', 'approval')):
            raise NeedsProductionConnection('The finished story no longer matches its production review. Your media has been preserved.')


def teaser(stories):
    """Use only finished editorial titles; never invent links between stories."""
    titles = [str(story.get('displayTitle') or story['title']).strip().rstrip('.!?') for story in stories]
    quoted = [f'“{title}”' for title in titles]
    subjects = ' and '.join(quoted) if len(quoted) == 2 else ', '.join(quoted[:-1])+', and '+quoted[-1]
    return f'Your newscast puts {subjects} in perspective.'


def run_job(job, report, guard, root, *, handoff=None):
    import produce_film

    if handoff is None:
        raise NeedsProductionConnection('Connect story production to finish your newscast. Your choices are saved.')
    guard()
    prepared = []
    # Review the entire request before starting an expensive partial cast.
    for chosen in job['stories']:
        record = handoff.get(chosen['id'], 'live').get('selection')
        approval = (record or {}).get('approval')
        if not approval or not (record or {}).get('prepared'):
            raise NeedsProductionConnection('Your stories are saved. Automatic writing and original imagery need a generation connection before this newscast can be made.')
        record = handoff._guard(chosen['id'], 'live', approval['id'])
        check_evidence(chosen, record)
        packet = copy.deepcopy(record['prepared']['packet'])
        packet['selection'] = handoff._lineage(record)
        prepared.append((chosen, approval['id'], packet))

    def current_authority():
        guard()
        for chosen, approval_id, _ in prepared:
            record = handoff._guard(chosen['id'], 'live', approval_id)
            check_evidence(chosen, record)

    finished = []
    for index, (chosen, _, packet) in enumerate(prepared):
        current_authority()
        report('sourcing', 'Checking the reporting', completed=index, storyId=chosen['id'])

        def progress(stage):
            current_authority()
            if stage in STAGE_AFTER:
                key, message = STAGE_AFTER[stage]
                report(key, message, completed=index, storyId=chosen['id'])

        story = produce_film.produce(packet, publish_result=False,
                                     completion_guard=current_authority, on_stage=progress)
        current_authority()
        story = copy.deepcopy(story)
        story.setdefault('production', {})['newscast'] = {
            'jobId': job['id'], 'eventId': chosen['id'], 'sourceRevision': chosen['revision'],
        }
        finished.append(story)
        report('checking', 'Checking the finished story', completed=index+1, storyId=chosen['id'])

    current_authority()
    voice = job['preferences']['voice']
    pace = .92 if job['preferences']['pace'] == 'unhurried' else 1
    duration = sum(story['voices'][voice]['duration']/pace for story in finished) + 1.5*(len(finished)-1)
    return {'stories': finished, 'teaser': teaser(finished), 'duration': round(duration, 3)}
