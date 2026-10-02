"""Small local client for the Top stories preparation queue; no model SDK needed."""
import argparse
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(port, payload=None):
    endpoint = '/api/top-stories/jobs' if payload is None else '/api/top-stories/prepare'
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = Request(f'http://127.0.0.1:{port}{endpoint}', data=data,
                  headers={'Content-Type': 'application/json'} if data is not None else {})
    try:
        with urlopen(req, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        try:
            detail = json.load(exc).get('error', str(exc))
        except (ValueError, OSError):
            detail = str(exc)
        raise RuntimeError(detail) from exc
    except URLError as exc:
        raise RuntimeError('The local Bearing server is not available; no queue state was changed.') from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8796)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('jobs')
    claim = sub.add_parser('claim')
    claim.add_argument('job_id')
    claim.add_argument('--out', required=True, help='Save the temporary claim/lease inside ignored output/.')
    submit = sub.add_parser('submit')
    submit.add_argument('receipt', help='JSON containing action, jobId, leaseToken, and item or hold reason.')
    args = parser.parse_args()
    try:
        if args.command == 'jobs':
            result = request(args.port)
        elif args.command == 'claim':
            output = Path(args.out).resolve()
            allowed = Path(__file__).resolve().parents[2] / 'output'
            if not output.is_relative_to(allowed.resolve()):
                raise ValueError('Save preparation leases only under this project\'s ignored output directory.')
            result = request(args.port, {'action': 'claim', 'jobId': args.job_id})
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            result = {'jobId': result['id'], 'state': result['state'], 'leaseUntil': result['leaseUntil'], 'saved': str(output)}
        else:
            payload = json.loads(Path(args.receipt).read_text(encoding='utf-8'))
            if payload.get('action') not in ('complete', 'hold'):
                raise ValueError('A receipt must complete or hold one claimed tile.')
            result = request(args.port, payload)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
