import json
from pathlib import Path

from openatlas import app


def vocabs_import() -> str:
    out = 'script started<br><br>'
    with open(Path(app.root_path) / '../install/indigo.json', 'r') as f:
        for data in json.load(f):
            if '@id' not in data or not data['@id'] \
                    .startswith('https://vocabs.acdh.oeaw.ac.at/indigo/'):
                continue
            out += 'Label: '
            if 'http://www.w3.org/2004/02/skos/core#prefLabel' in data:
                for item in \
                        data['http://www.w3.org/2004/02/skos/core#prefLabel']:
                    if '@language' in item and item['@language'] == 'en':
                        out += item['@value']
                        break
            else:
                out += 'N/A'
            out += '<br>Vocabs id: '
            if '@id' in data:
                out += data['@id'] \
                    .replace('https://vocabs.acdh.oeaw.ac.at/indigo/', '')
            else:
                out += 'N/A'
            out += '<br>---<br>'
            for key, value in data.items():
                if key in [
                        '@id',
                        '@type',
                        'http://www.w3.org/2004/02/skos/core#topConceptOf',
                        'http://www.w3.org/2004/02/skos/core#inScheme',
                        'http://www.w3.org/2004/02/skos/core#prefLabel']:
                    continue
                out += f'{key}: {value}<br>'
            out += '<br><br>'
    out += '<br>script ended'
    return out
