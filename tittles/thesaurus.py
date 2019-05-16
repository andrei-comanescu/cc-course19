import requests
import xml.etree.ElementTree as ET
from collections import Counter
from nltk.corpus import wordnet as wn

def _query(category, modifier):
    """Query Thesaurus Rex and return results with normalized weights"""
    r = requests.get('http://ngrams.ucd.ie/therex3/common-nouns/category.action',
                     params={'cate': f'{modifier}:{category}', 'xml': 'true'})
    root = ET.fromstring(r.text)
    members = {m.text.strip(): int(m.attrib['weight']) for m in root.iter('Member')}
    members = {k: v / max(members.values()) for k, v in members.items()}
    return members

def find_nuances(category):
    """Find adjectives for category."""
    r = requests.get('http://ngrams.ucd.ie/therex3/common-nouns/member.action',
                     params={'kw': category, 'xml': 'true'})
    root = ET.fromstring(r.text)
    members = {m.text.strip(): int(m.attrib['weight']) for m in root.iter('Modifier')}
    members = {k: v / max(members.values()) for k, v in members.items()}
    return members

def find_members(category, adjectives):
    """
    Find suggested members from Thesaurus Rex based on category and adjectives.

    Args:
        Category (str) : category for the member
        Adjectives (list of str) : adjectives describing the member

    Returns:
        Dictionary: key str : member name and value float [0, 1] : how relevant
        the suggestion is (high being better).
    """
    weights = Counter()
    counts = Counter()
    for adjective in adjectives:
        members = _query(category, adjective)
        weights.update(members)
        counts.update(members.keys())
    members = weights.keys()
    return {m: ((counts[m] - 1) / (len(adjectives) - 1) + weights[m] / len(adjectives)) / 2
            for m in members}

def find_synonyms(word):
    """Find synonyms from WordNet"""
    words = set()
    for s in wn.synsets(word, pos=wn.ADJ):
        words |= set(s.lemma_names())
        for a in s.similar_tos():
            words |= set(a.lemma_names())
        for a in s.also_sees():
            words |= set(a.lemma_names())
    return words

if __name__ == "__main__":
    import sys
    sys.path.insert(0,'..')
    import inputs
    emotion, word_pairs = inputs.get_input(False)

    category = next(word_pair[1] for word_pair in word_pairs if word_pair[0] == 'activity')
    print('activity:', category)
    suggestions = find_nuances(category)
    for suggestion in Counter(suggestions).most_common(10):
        print(f'  {suggestion[1]:.2f} {suggestion[0]}')

    category = next(word_pair[1] for word_pair in word_pairs if word_pair[0] == 'weather')
    print('weather:', category)
    suggestions = find_nuances(category)
    for suggestion in Counter(suggestions).most_common(10):
        print(f'  {suggestion[1]:.2f} {suggestion[0]}')

    category = next(word_pair[1] for word_pair in word_pairs if word_pair[0] == 'location')
    print('location:', category)
    suggestions = find_nuances(category)
    for suggestion in Counter(suggestions).most_common(10):
        print(f'  {suggestion[1]:.2f} {suggestion[0]}')

    adjectives = list(word_pair[1] for word_pair in word_pairs if word_pair[0] == 'human')
    print('human:')
    print(' adjectives:', ', '.join(adjectives))
    print(' suggestions:')
    suggestions = find_members('person', adjectives)
    for suggestion in Counter(suggestions).most_common(10):
        print(f'  {suggestion[1]:.2f} {suggestion[0]}')

    adjectives = list(word_pair[1] for word_pair in word_pairs if word_pair[0] == 'animal')
    print('animal:')
    print(' adjectives:', ', '.join(adjectives))
    print(' suggestions:')
    suggestions = find_members('animal', adjectives)
    for suggestion in Counter(suggestions).most_common(10):
        print(f'  {suggestion[1]:.2f} {suggestion[0]}')
