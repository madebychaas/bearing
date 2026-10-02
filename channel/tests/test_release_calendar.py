import json
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'production'))
import release_calendar as calendar

NOW = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)


def document(*events):
    return ('BEGIN:VCALENDAR\r\nVERSION:2.0\r\n' + ''.join(events) + 'END:VCALENDAR\r\n').encode()


def event(uid='trade', start='20261006T123000Z', title='Trade release', extra=''):
    return f'BEGIN:VEVENT\r\nUID:{uid}\r\nSUMMARY:{title}\r\nDTSTART:{start}\r\n{extra}END:VEVENT\r\n'


class ReleaseCalendarTests(unittest.TestCase):
    def test_folded_titles_escapes_and_utc_are_preserved(self):
        data = document(event(title='Personal income\\,\r\n  spending\\; savings'))
        row = calendar.parse_calendar(data)[0]
        self.assertEqual(row['title'], 'Personal income, spending; savings')
        self.assertEqual(row['scheduledAt'], '2026-10-06T12:30:00Z')
        self.assertEqual(row['sourceUrl'], calendar.SOURCE_URL)

    def test_date_only_and_floating_times_are_not_invented(self):
        data = document(event('date', '20261006'), event('floating', '20261006T083000'), event('real'))
        self.assertEqual(len(calendar.parse_calendar(data)), 1)
        declared = event().replace('DTSTART:', 'DTSTART;VALUE=DATE:')
        self.assertEqual(calendar.parse_calendar(document(declared)), [])

    def test_explicit_timezone_and_ambiguous_local_times(self):
        east = event(start='20261006T083000').replace('DTSTART:', 'DTSTART;TZID=America/New_York:')
        ambiguous = event('fall', '20261101T013000').replace('DTSTART:', 'DTSTART;TZID=America/New_York:')
        rows = calendar.parse_calendar(document(east, ambiguous))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['scheduledAt'], '2026-10-06T12:30:00Z')

    def test_duplicate_revisions_and_cancellation_do_not_resurrect(self):
        old = event(extra='SEQUENCE:1\r\n')
        new = event(start='20261007T123000Z', extra='SEQUENCE:2\r\n')
        rows = calendar.parse_calendar(document(new, old, new))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['scheduledAt'], '2026-10-07T12:30:00Z')
        cancel = 'BEGIN:VEVENT\r\nUID:trade\r\nSEQUENCE:3\r\nSTATUS:CANCELLED\r\nEND:VEVENT\r\n'
        self.assertEqual(calendar.parse_calendar(document(cancel, old, new)), [])

    def test_empty_read_is_network_free_and_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(calendar, 'fetch') as fetch:
            result = calendar.snapshot(folder, NOW)
            self.assertEqual(result['events'], [])
            self.assertEqual(result['health']['status'], 'not-checked')
            self.assertFalse((Path(folder) / 'production').exists())
            fetch.assert_not_called()

    def test_window_due_does_not_claim_publication_and_local_now_is_converted(self):
        body = document(event('old', '20261002T055959Z'), event('due', '20261002T100000Z'),
                        event('next', '20261009T115959Z'), event('far', '20261009T120001Z'))
        with tempfile.TemporaryDirectory() as folder, patch.object(calendar, 'fetch', return_value={'status': 200, 'body': body}):
            calendar.refresh(folder, NOW)
            result = calendar.snapshot(folder, NOW.astimezone(timezone(timedelta(hours=-5))))
            self.assertEqual([x['status'] for x in result['events']], ['due', 'scheduled'])
            self.assertTrue(all('publication has not been confirmed' in x['note'] for x in result['events']))
            self.assertFalse(result['health']['stale'])

    def test_hourly_conditional_refresh_and_304_keep_events(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(calendar, 'fetch', return_value={'status': 200, 'body': document(event()), 'etag': 'rev1', 'modified': 'date1'}) as fetch:
                first = calendar.refresh(folder, NOW)
                calendar.refresh(folder, NOW + timedelta(minutes=59))
                self.assertEqual(fetch.call_count, 1)
            with patch.object(calendar, 'fetch', return_value={'status': 304}) as fetch:
                second = calendar.refresh(folder, NOW + timedelta(hours=1))
                self.assertEqual(fetch.call_args.args[0], {'If-None-Match': 'rev1', 'If-Modified-Since': 'date1'})
                self.assertEqual(first['events'], second['events'])
                self.assertEqual(second['health']['status'], 'unchanged')

    def test_failure_retains_good_schedule_with_error_and_backoff(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(calendar, 'fetch', return_value={'status': 200, 'body': document(event())}):
                good = calendar.refresh(folder, NOW)
            with patch.object(calendar, 'fetch', side_effect=OSError('Connection unavailable')) as fetch:
                failed = calendar.refresh(folder, NOW + timedelta(hours=1))
                calendar.refresh(folder, NOW + timedelta(minutes=90))
                self.assertEqual(fetch.call_count, 1)
                self.assertEqual(failed['events'][0]['id'], good['events'][0]['id'])
                self.assertEqual(failed['health']['lastSuccess'], good['health']['lastSuccess'])
                self.assertTrue(failed['health']['stale'])
                self.assertIn('may be stale', failed['events'][0]['note'])
                self.assertIn('Connection unavailable', failed['health']['error'])

    def test_retry_after_and_cache_control_can_extend_hour_floor(self):
        with tempfile.TemporaryDirectory() as folder:
            exc = urllib.error.HTTPError(calendar.CALENDAR_URL, 429, 'Too many requests', {'Retry-After': '7200'}, None)
            with patch.object(calendar, 'fetch', side_effect=exc):
                result = calendar.refresh(folder, NOW)
                self.assertEqual(result['health']['nextCheckAt'], '2026-10-02T14:00:00Z')
        self.assertEqual(calendar._delay({'cacheControl': 'public, max-age=10800'}), timedelta(hours=3))

    def test_invalid_response_cannot_replace_good_calendar(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(calendar, 'fetch', return_value={'status': 200, 'body': document(event())}):
                calendar.refresh(folder, NOW)
            with patch.object(calendar, 'fetch', return_value={'status': 200, 'body': b'<html>Temporarily unavailable</html>'}):
                result = calendar.refresh(folder, NOW + timedelta(hours=1))
                self.assertEqual(len(result['events']), 1)
                self.assertTrue(result['health']['stale'])
        with self.assertRaises(ValueError):
            calendar.parse_calendar(document(event())[:-40])
        with self.assertRaises(ValueError):
            calendar.parse_calendar(b'x' * (calendar.MAX_BYTES + 1))

    def test_result_is_bounded_and_old_quarter_records_stay_out(self):
        items = [event(str(i), f'20261003T{i:02d}0000Z') for i in range(15)]
        items.append(event('old-quarter', '20250130T133000Z'))
        with tempfile.TemporaryDirectory() as folder, patch.object(calendar, 'fetch', return_value={'status': 200, 'body': document(*items)}):
            result = calendar.refresh(folder, NOW)
            self.assertEqual(len(result['events']), 12)
            self.assertEqual(result['events'][0]['scheduledAt'], '2026-10-03T00:00:00Z')

    def test_unreadable_cache_is_reported_without_raising(self):
        with tempfile.TemporaryDirectory() as folder:
            path = calendar._cache_path(folder)
            path.parent.mkdir(parents=True)
            path.write_text('{bad', encoding='utf-8')
            result = calendar.snapshot(folder, NOW)
            self.assertEqual(result['events'], [])
            self.assertIn('could not be read', result['health']['error'])


if __name__ == '__main__':
    unittest.main()
