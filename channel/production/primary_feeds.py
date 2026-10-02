"""Small official-document discovery adapters; no generated source excerpts."""
import json
from datetime import datetime
from urllib.parse import urlsplit


def parse_inspection(body):
    value = json.loads(body)
    if not isinstance(value, dict) or not isinstance(value.get('results'), list):
        raise ValueError('Public inspection response has no document list')
    entries = []
    for item in value['results'][:200]:
        if not isinstance(item, dict):
            continue
        title, url, filed = item.get('title'), item.get('html_url'), item.get('filed_at')
        if not all(isinstance(value, str) and value.strip() for value in (title, url, filed)):
            continue
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname != 'www.federalregister.gov' or parsed.username or parsed.password:
            continue
        try:
            when = datetime.fromisoformat(filed.replace('Z', '+00:00'))
            if when.tzinfo is None:
                continue
        except ValueError:
            continue
        entries.append({'title': title, 'link': url, 'description': '', 'published': filed,
                        'timestampKind': 'filed', 'filing': {
                            'documentNumber': item.get('document_number'),
                            'type': item.get('type'), 'publicationDate': item.get('publication_date'),
                            'agencies': [agency['name'] for agency in item.get('agencies', []) if isinstance(agency, dict) and isinstance(agency.get('name'), str)],
                            'note': 'Public-inspection filing; planned publication is a separate date. Confirm document type, legal status and effective date in the official document.'}})
    return entries
