#!/usr/bin/env python3
"""Structural, continuity, translation-presence and app-isolation checks for TomEng Host."""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / 'content' / 'host'
read = lambda name: json.loads((HOST / name).read_text(encoding='utf-8'))
phrases = read('phrases.host.v1.json')
lessons = read('lessons.host.v1.json')
categories = read('categories.host.v1.json')
subcategories = read('subcategories.host.v1.json')
patterns = read('patterns.host.v1.json')
core = json.loads((HOST / 'tomeng-common-core.json').read_text(encoding='utf-8'))
by_id = {phrase['id']: phrase for phrase in phrases}
assert len(phrases) == 1200 and len(by_id) == 1200
assert set(by_id) == {f'p{i:03d}' for i in range(1, 1201)}
assert len(lessons) == 258
assert len(categories) == 12
assert len(subcategories) == 56

common_ids = {p['id'] for p in core['phrases']}
common = [p for p in phrases if p['id'] in common_ids]
host = [p for p in phrases if p.get('source') == 'tomeng_host_v1']
assert len(common_ids) == len(common) == 625
assert len(host) == 575 and not (common_ids & {p['id'] for p in host})
assert Counter(p['categoryId'] for p in common) == {'everyday': 500, 'reflex': 125}
for phrase in common:
    source = next(item for item in core['phrases'] if item['id'] == phrase['id'])
    for key in ('id', 'en', 'vi', 'context', 'follow'):
        assert phrase[key] == source[key], (phrase['id'], key)

expected_host_counts = {'rooms':60, 'booking':60, 'checkin':60, 'housekeeping':55, 'maintenance':60,
                        'complaints':60, 'billing':55, 'safety':55, 'team':55, 'messaging':55}
host_counts = Counter(p['categoryId'] for p in host)
assert dict(host_counts) == expected_host_counts
assert Counter(p['categoryId'] for p in phrases) == {'everyday':500, 'reflex':125, **expected_host_counts}
phrase_pattern_ids = {p['patternId'] for p in phrases}
assert len(phrase_pattern_ids) == len(patterns) == len({p['id'] for p in patterns})
assert phrase_pattern_ids == {p['id'] for p in patterns}

required = ('id', 'en', 'vi', 'context', 'follow', 'pattern', 'memoryTip', 'categoryId', 'subCategoryId', 'patternId')
for phrase in host:
    assert all(str(phrase.get(key, '')).strip() for key in required), phrase['id']
    assert phrase['level'] in ('A2-B1', 'A1-A2', 'B1-B2')
    assert phrase['language'] == 'en-US' and phrase['role'] in ('host-to-guest', 'host-to-team')
    assert not re.search(r'\{[^}]+\}|\b(?:the the|a a|the a|unit unit|instead instead|by within|by before|at before|at after|until within|until after)\b', phrase['en'], re.I), (phrase['id'], phrase['en'])
    assert not re.search(r'(?:p\.m\.|a\.m\.)\.$', phrase['en']), (phrase['id'], phrase['en'])
    assert not any(code in phrase['en'] for code in ('4821', '7350', '9164', '2608'))

host_lessons = [lesson for lesson in lessons if lesson['primaryCategoryId'] in expected_host_counts]
assert len(host_lessons) == 115
covered = []
for lesson in host_lessons:
    ids = lesson['candidatePhraseIds']
    assert len(ids) == len(lesson['phraseIds']) == len(lesson['steps']) == 5, lesson['id']
    assert ids == lesson['phraseIds'] == [step['phraseId'] for step in lesson['steps']]
    assert len(set(ids)) == 5
    assert all(by_id[phrase_id]['categoryId'] == lesson['primaryCategoryId'] for phrase_id in ids)
    assert all(step['turn'] == index + 1 and step['kind'] == 'new' for index, step in enumerate(lesson['steps']))
    assert all(by_id[ids[i]]['follow'] == by_id[ids[i + 1]]['en'] for i in range(4)), lesson['id']
    assert lesson['scenarioTitle'] and lesson['scenarioGoal'] and lesson['scenarioContext'] and lesson['practicePrompt']
    covered.extend(ids)
assert len(covered) == len(set(covered)) == 575
assert set(covered) == {p['id'] for p in host}

with (HOST / 'SCENARIO_MAPPING_HOST_V1.csv').open(encoding='utf-8-sig', newline='') as handle:
    mapping = list(csv.DictReader(handle))
assert len(mapping) == len(lessons)
assert all(int(row['phrase_count']) == 5 and 1 <= len(row['candidate_ids'].split()) <= 5 for row in mapping)
preview = (HOST / 'PREVIEW_14_DAYS.md').read_text(encoding='utf-8')
assert len(re.findall(r'^## Ngày \d{3}', preview, re.M)) == 14

browser_phrases = json.loads((ROOT / 'data.js').read_text(encoding='utf-8').split('=', 1)[1].rstrip(';\n'))
browser_meta = json.loads((ROOT / 'meta.js').read_text(encoding='utf-8').split('=', 1)[1].rstrip(';\n'))
assert browser_phrases == phrases
assert browser_meta == {'categories':categories, 'subcategories':subcategories, 'patterns':patterns, 'lessons':lessons, 'contentVersion':'host-v1.0.0', 'trackIds':['everyday','host','mixed']}
manifest = json.loads((ROOT / 'manifest.webmanifest').read_text(encoding='utf-8'))
assert manifest['name'].startswith('TomEng Host') and manifest['scope'] == './' and manifest['id'] == './'
assert 'host-icon-192.png' in (ROOT / 'sw.js').read_text(encoding='utf-8')
assert 'tomeng_native_v3' not in (ROOT / 'app.js').read_text(encoding='utf-8')
print('PASS: 1,200 IDs; 625 common IDs retained; 575 Host IDs across 115 linked scenarios; 258 lessons; track counts; generated data; 14-day preview; Host namespace/PWA identity')
