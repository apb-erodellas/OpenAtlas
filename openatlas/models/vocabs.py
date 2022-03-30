import json
from pathlib import Path

from openatlas import app
from openatlas.database.connect import Transaction
from openatlas.models.entity import Entity


def vocabs_import() -> str:
    entities = {
        'graffiti_type': Entity.get_by_id(107),
        'wikidata': Entity.get_by_id(103),
        'getty': Entity.get_by_id(105),
        'vocabs': Entity.get_by_id(106),
        'exact': Entity.get_by_id(12),
        'close': Entity.get_by_id(13)}
    types = {}
    missing = ''
    vocabs = 'https://vocabs.acdh.oeaw.ac.at/indigo/'
    skos = 'http://www.w3.org/2004/02/skos/core'
    wikidata = 'https://www.wikidata.org/wiki/'
    getty = 'http://vocab.getty.edu/page/aat/'
    with open(Path(app.root_path) / '../install/indigo.json', 'r') as f:
        for data in json.load(f):
            if '@id' not in data \
                    or not data['@id'] != f'{vocabs}Thesaurus' \
                    or not data['@id'].startswith(vocabs):
                continue
            id_ = int(data['@id'].replace(vocabs, ''))
            label = 'N/A'
            if f'{skos}#prefLabel' in data:
                for item in data[f'{skos}#prefLabel']:
                    if '@language' in item and item['@language'] == 'en':
                        label = item['@value']
                        break
            types[id_] = {
                'vocabs_id': id_,
                'label': label,
                'subs': [],
                'super_id': None,
                'openatlas_id': None,
                'references': {'wikidata': [], 'getty': []}}

            if f'{skos}#member' in data:
                for sub in data[f'{skos}#member']:
                    types[id_]['subs'].append(
                       int(sub['@id'].replace(vocabs, '')))

            # External references
            for match in ['exact', 'close']:
                if f'{skos}#{match}Match' in data:
                    items = data[f'{skos}#{match}Match']
                    for reference in items:
                        if reference['@id'].startswith(wikidata):
                            types[id_]['references']['wikidata'].append({
                                'id': reference['@id'].replace(wikidata, ''),
                                'match': match})
                        elif reference['@id'].startswith(getty):
                            types[id_]['references']['getty'].append({
                                'id': reference['@id'].replace(getty, ''),
                                'match': match})
                        else:
                            missing += f'{reference}<br>'

            for key, value in data.items():
                if key in [
                        '@id',
                        '@type',
                        'http://purl.org/dc/terms/source',
                        f'{skos}#altLabel',
                        f'{skos}#example',
                        f'{skos}#related',
                        f'{skos}#topConceptOf',
                        f'{skos}#inScheme',
                        f'{skos}#prefLabel',
                        f'{skos}#member',
                        f'{skos}#exactMatch',
                        f'{skos}#closeMatch',
                        f'{skos}#broadMatch',
                        f'{skos}#relatedMatch',
                        f'{skos}#broader',
                        f'{skos}#narrower']:
                    continue
                missing += f'{label} ({id_}) {key}: {value}<br>'
    # Set super id
    for vocabs_id, item in types.items():
        for sub_id in item['subs']:
            if types[sub_id]['super_id']:
                missing += f'Too many parents for {types[sub_id]}<br>'
            else:
                types[sub_id]['super_id'] = vocabs_id

    Transaction.begin()

    # Insert types and their external references
    for vocabs_id, item in types.items():
        entity = Entity.insert(
            'type',
            item['label'],
            'Imported from Vocabs on 2022-03-30')
        item['openatlas_id'] = entity.id
        entities['vocabs'].link(
            'P67',
            entity,
            str(vocabs_id),
            type_id=entities['exact'].id)
        for system_name, links in item['references'].items():
            for link_ in links:
                entities[system_name].link(
                    'P67',
                    entity,
                    link_['id'],
                    type_id=entities[link_['match']].id)

    # Link types to super
    for item in types.values():
        entity = Entity.get_by_id(item['openatlas_id'])
        if item['super_id']:
            entity.link(
                'P127',
                Entity.get_by_id(types[item['super_id']]['openatlas_id']))
        else:
            entity.link('P127', entities['graffiti_type'])

    Transaction.commit()

    out = ''
    for item in types.values():
        out += f'vocabs id: {item["vocabs_id"]}<br>'
        out += f'label: {item["label"]}<br>'
        out += f'parent: {item["super_id"]}<br>' if item['super_id'] else ''
        out += f'subs: {item["subs"]}<br>' if item['subs'] else ''
        for system_name, links in item['references'].items():
            for link_ in links:
                out += f"{system_name} id: {link_['id']}, {link_['match']}<br>"
        out += '---<br>'
    return f'{out} {missing}'
