"""Kobo API v2, with same-origin pagination and no raw data files/logging."""
import json
import re
import time
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def fetch(server, asset_uid, token):
    origin = urlsplit(server)
    if origin.scheme != 'https' or not origin.netloc or origin.username or origin.password or origin.path not in ('', '/') or origin.query or origin.fragment:
        raise ValueError('KOBO_SERVER must be an HTTPS origin, e.g. https://eu.kobotoolbox.org')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', asset_uid):
        raise ValueError('Invalid asset UID')
    if not token or any(c.isspace() for c in token):
        raise ValueError('Missing or invalid Kobo token')
    url = server.rstrip('/') + '/api/v2/assets/' + asset_uid + '/data/?limit=1000'
    opener = build_opener(NoRedirect)
    records, visited = [], set()
    while url:
        target = urlsplit(url)
        if (target.scheme, target.netloc) != (origin.scheme, origin.netloc) or target.username or target.password:
            raise ValueError('Refusing cross-origin pagination')
        if url in visited:
            raise ValueError('Pagination loop')
        visited.add(url)
        for attempt in range(4):
            try:
                with opener.open(Request(url, headers={'Authorization': 'Token ' + token, 'Accept': 'application/json'}), timeout=60) as response:
                    payload = json.load(response)
                break
            except HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise RuntimeError('Kobo request failed (HTTP %s)' % exc.code) from None
            except URLError:
                if attempt == 3:
                    raise RuntimeError('Unable to reach Kobo server') from None
            time.sleep(2 ** attempt)
        if not isinstance(payload, dict) or not isinstance(payload.get('results'), list) or any(not isinstance(r, dict) for r in payload['results']):
            raise ValueError('Unexpected Kobo response format')
        records.extend(payload['results'])
        next_page = payload.get('next')
        if next_page is not None and not isinstance(next_page, str):
            raise ValueError('Invalid pagination link')
        url = urljoin(url, next_page) if next_page else None
    return records
