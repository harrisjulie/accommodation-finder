#!/usr/bin/env python3
"""
Find and add missing disabilities from the parsed document.
"""

import json
from difflib import SequenceMatcher

def load_json(filepath):
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Save JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def similarity(a, b):
    """Calculate similarity between two strings."""
    a = a.lower().strip()
    b = b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()

def find_best_match(name, entities, threshold=0.7):
    """Find the best matching entity by name."""
    best_match = None
    best_score = 0

    for entity in entities:
        entity_name = entity['name']
        score = similarity(name, entity_name)

        # Also check if one is contained in the other
        if name.lower() in entity_name.lower() or entity_name.lower() in name.lower():
            score = max(score, 0.85)

        if score > best_score:
            best_score = score
            best_match = entity

    if best_score >= threshold:
        return best_match, best_score

    return None, 0

def categorize_disability(name):
    """Categorize disability based on name."""
    name_lower = name.lower()

    if any(word in name_lower for word in ['arthritis', 'pain', 'back', 'leg', 'amputation', 'injury', 'impairment']):
        return 'Physical/Mobility'
    elif any(word in name_lower for word in ['anxiety', 'depression', 'bipolar', 'ptsd', 'ocd', 'schizophrenia', 'phobia', 'mental', 'personality', 'eating disorder']):
        return 'Mental Health'
    elif any(word in name_lower for word in ['adhd', 'autism', 'learning', 'intellectual', 'brain', 'alzheimer', 'parkinson', 'huntington', 'dystonia', 'tremor']):
        return 'Neurological/Cognitive'
    elif any(word in name_lower for word in ['blind', 'vision', 'low vision', 'colorblind', 'albinism']):
        return 'Visual'
    elif any(word in name_lower for word in ['deaf', 'hearing', 'auditory']):
        return 'Hearing'
    elif any(word in name_lower for word in ['diabetes', 'heart', 'cancer', 'lupus', 'crohn', 'kidney', 'renal', 'hepatitis', 'hiv', 'aids', 'disease', 'syndrome']):
        return 'Chronic Health'
    elif any(word in name_lower for word in ['allergy', 'asthma', 'respiratory', 'breathing', 'fragrance', 'chemical']):
        return 'Allergies/Sensitivities'
    else:
        return 'Other'

def main():
    print("Finding missing disabilities...")

    # Load data
    disabilities = load_json('/home/user/accommodation-finder/disabilities.json')
    parsed_data = load_json('/home/user/accommodation-finder/parsed_disabilities.json')

    missing_disabilities = []

    # Find missing disabilities
    for disability_name in parsed_data.keys():
        match, score = find_best_match(disability_name, disabilities)

        if not match:
            missing_disabilities.append(disability_name)

    print(f"\nFound {len(missing_disabilities)} missing disabilities:")
    for name in missing_disabilities:
        print(f"  - {name}")

    if not missing_disabilities:
        print("\n✓ All disabilities already exist in the database!")
        return

    # Add missing disabilities
    print("\nAdding missing disabilities...")

    # Find next available ID
    existing_ids = [d['id'] for d in disabilities]
    max_num = max([int(id[1:]) for id in existing_ids])

    for i, disability_name in enumerate(missing_disabilities):
        new_id = f"D{str(max_num + i + 1).zfill(3)}"
        category = categorize_disability(disability_name)

        new_disability = {
            'id': new_id,
            'name': disability_name,
            'category': category,
            'description': ''
        }

        disabilities.append(new_disability)
        print(f"  Added: {new_id} - {disability_name} ({category})")

    # Save updated disabilities
    save_json('/home/user/accommodation-finder/disabilities.json', disabilities)

    print(f"\n✓ Added {len(missing_disabilities)} new disabilities!")
    print(f"Total disabilities: {len(disabilities)}")

if __name__ == '__main__':
    main()
