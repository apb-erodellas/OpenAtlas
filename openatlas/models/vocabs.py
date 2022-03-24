import json
from pathlib import Path

from openatlas import app


def vocabs_import() -> str:
    types = {}
    missing = ''
    with open(Path(app.root_path) / '../install/indigo.json', 'r') as f:
        for data in json.load(f):
            if '@id' not in data \
                    or not data['@id'] != 'https://vocabs.acdh.oeaw.ac.at/indigo/Thesaurus' \
                    or not data['@id'].startswith('https://vocabs.acdh.oeaw.ac.at/indigo/'):
                continue
            id_ = data['@id'].replace('https://vocabs.acdh.oeaw.ac.at/indigo/', '')
            label = 'N/A'
            if 'http://www.w3.org/2004/02/skos/core#prefLabel' in data:
                for item in data['http://www.w3.org/2004/02/skos/core#prefLabel']:
                    if '@language' in item and item['@language'] == 'en':
                        label = item['@value']
                        break
            types[id_] = {'vocabs_id': id_, 'label': label, 'subs': []}

            if 'http://www.w3.org/2004/02/skos/core#member' in data:
                subs = data['http://www.w3.org/2004/02/skos/core#member']
                for sub in subs:
                    types[id_]['subs'].append(sub['@id'].replace('https://vocabs.acdh.oeaw.ac.at/indigo/', ''))

            for key, value in data.items():
                if key in [
                        'http://www.w3.org/2004/02/skos/core#exactMatch',
                        'http://www.w3.org/2004/02/skos/core#closeMatch',
                        '@id',
                        '@type',
                        'http://purl.org/dc/terms/source',
                        'http://www.w3.org/2004/02/skos/core#altLabel',
                        'http://www.w3.org/2004/02/skos/core#example',
                        'http://www.w3.org/2004/02/skos/core#related',
                        'http://www.w3.org/2004/02/skos/core#topConceptOf',
                        'http://www.w3.org/2004/02/skos/core#inScheme',
                        'http://www.w3.org/2004/02/skos/core#prefLabel',
                        'http://www.w3.org/2004/02/skos/core#member',
                        'http://www.w3.org/2004/02/skos/core#broadMatch',
                        'http://www.w3.org/2004/02/skos/core#relatedMatch',
                        'http://www.w3.org/2004/02/skos/core#broader',
                        'http://www.w3.org/2004/02/skos/core#narrower']:
                    continue
                missing += f'{label} ({id_}) {key}: {value}<br>'
    out = ''
    for item in types.values():
        out += f'vocabs id: {item["vocabs_id"]}<br>'
        out += f'label: {item["label"]}<br>'
        out += f'subs: {item["subs"]}<br>'
        out += '---<br>'
    return f'{out} {missing}'
