#!/usr/bin/env python3
"""
Build complete relationships between disabilities, limitations, barriers, and accommodations
based on the parsed document data.
"""

import json
import re
from difflib import SequenceMatcher
from collections import defaultdict

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

def normalize_accommodation_name(name):
    """Normalize accommodation name for better matching."""
    # Remove common prefixes
    name = re.sub(r'^(Products|Services|Strategies|Other|Phone|Magnification|Industrial|Office Equipment|Agriculture/Farm|Office or Retail Goods|People|Living Independently|Moving Around|Working at Heights|Working Safely|Independent Living|Mobility Aids|Sensitivity to Cold|Sensitivity to Heat)\s*[-:]*\s*', '', name, flags=re.IGNORECASE)

    # Clean up extra spaces
    name = ' '.join(name.split())

    return name.strip()

def get_or_create_entity(name, entities_list, entity_type, category='General'):
    """Get existing entity or create new one."""
    # Find existing
    match, score = find_best_match(name, entities_list)

    if match:
        return match['id'], False

    # Create new entity
    # Find next available ID
    prefix = entity_type[0]  # D, L, B, A
    existing_ids = [e['id'] for e in entities_list if e['id'].startswith(prefix)]

    if existing_ids:
        max_num = max([int(id[1:]) for id in existing_ids])
        new_id = f"{prefix}{str(max_num + 1).zfill(3)}"
    else:
        new_id = f"{prefix}001"

    new_entity = {
        'id': new_id,
        'name': name,
        'category': category,
        'description': ''
    }

    entities_list.append(new_entity)

    return new_id, True

def main():
    print("Loading existing data files...")

    # Load existing data
    disabilities = load_json('/home/user/accommodation-finder/disabilities.json')
    limitations = load_json('/home/user/accommodation-finder/limitations.json')
    barriers = load_json('/home/user/accommodation-finder/barriers.json')
    accommodations = load_json('/home/user/accommodation-finder/accommodations.json')
    relationships = load_json('/home/user/accommodation-finder/relationships.json')

    # Load parsed data
    parsed_data = load_json('/home/user/accommodation-finder/parsed_disabilities.json')

    print(f"Loaded {len(disabilities)} disabilities")
    print(f"Loaded {len(limitations)} limitations")
    print(f"Loaded {len(barriers)} barriers")
    print(f"Loaded {len(accommodations)} accommodations")

    # Statistics
    stats = {
        'new_limitations': 0,
        'new_barriers': 0,
        'new_accommodations': 0,
        'disability_limitation_rels': 0,
        'disability_barrier_rels': 0,
        'limitation_accommodation_rels': 0,
        'barrier_accommodation_rels': 0,
        'disability_accommodation_rels': 0
    }

    # Initialize relationship structures
    if 'disability_limitations' not in relationships:
        relationships['disability_limitations'] = {}
    if 'disability_barriers' not in relationships:
        relationships['disability_barriers'] = {}
    if 'limitation_accommodations' not in relationships:
        relationships['limitation_accommodations'] = {}
    if 'barrier_accommodations' not in relationships:
        relationships['barrier_accommodations'] = {}
    if 'disability_accommodations' not in relationships:
        relationships['disability_accommodations'] = {}

    print("\nProcessing disabilities and building relationships...")

    # Process each disability
    for disability_name, data in parsed_data.items():
        print(f"\n{'='*60}")
        print(f"Processing: {disability_name}")
        print(f"{'='*60}")

        # Find or create disability
        disability_match, score = find_best_match(disability_name, disabilities)

        if not disability_match:
            print(f"  WARNING: Could not find disability '{disability_name}' in database")
            # Try some name variations
            variations = [
                disability_name,
                disability_name.replace("'", ""),
                disability_name.replace(" Disease", ""),
                disability_name.replace(" Disorder", ""),
                disability_name.replace(" Syndrome", ""),
            ]

            for var in variations:
                disability_match, score = find_best_match(var, disabilities)
                if disability_match:
                    print(f"  Found match using variation: {var} -> {disability_match['name']}")
                    break

        if not disability_match:
            print(f"  Skipping {disability_name}")
            continue

        disability_id = disability_match['id']
        print(f"  Disability ID: {disability_id} ({disability_match['name']})")

        # Initialize relationship arrays for this disability
        if disability_id not in relationships['disability_limitations']:
            relationships['disability_limitations'][disability_id] = []
        if disability_id not in relationships['disability_barriers']:
            relationships['disability_barriers'][disability_id] = []
        if disability_id not in relationships['disability_accommodations']:
            relationships['disability_accommodations'][disability_id] = []

        # Process limitations
        print(f"\n  Processing {len(data['limitations'])} limitations:")
        for limitation_name, accommodation_names in data['limitations'].items():
            print(f"    - {limitation_name} ({len(accommodation_names)} accommodations)")

            # Get or create limitation
            limitation_id, is_new = get_or_create_entity(
                limitation_name, limitations, 'Limitation', 'Functional'
            )

            if is_new:
                stats['new_limitations'] += 1
                print(f"      Created new limitation: {limitation_id}")

            # Add disability-limitation relationship
            if limitation_id not in relationships['disability_limitations'][disability_id]:
                relationships['disability_limitations'][disability_id].append(limitation_id)
                stats['disability_limitation_rels'] += 1

            # Initialize accommodation array for this limitation
            if limitation_id not in relationships['limitation_accommodations']:
                relationships['limitation_accommodations'][limitation_id] = []

            # Process accommodations for this limitation
            for acc_name in accommodation_names:
                acc_name_normalized = normalize_accommodation_name(acc_name)

                if not acc_name_normalized:
                    continue

                # Get or create accommodation
                acc_id, is_new = get_or_create_entity(
                    acc_name_normalized, accommodations, 'Accommodation', 'Workplace'
                )

                if is_new:
                    stats['new_accommodations'] += 1
                    print(f"      Created new accommodation: {acc_id} - {acc_name_normalized}")

                # Add limitation-accommodation relationship
                if acc_id not in relationships['limitation_accommodations'][limitation_id]:
                    relationships['limitation_accommodations'][limitation_id].append(acc_id)
                    stats['limitation_accommodation_rels'] += 1

                # Add disability-accommodation relationship (via limitation)
                if acc_id not in relationships['disability_accommodations'][disability_id]:
                    relationships['disability_accommodations'][disability_id].append(acc_id)
                    stats['disability_accommodation_rels'] += 1

        # Process barriers (work-related functions)
        print(f"\n  Processing {len(data['barriers'])} barriers:")
        for barrier_name, accommodation_names in data['barriers'].items():
            print(f"    - {barrier_name} ({len(accommodation_names)} accommodations)")

            # Get or create barrier
            barrier_id, is_new = get_or_create_entity(
                barrier_name, barriers, 'Barrier', 'Environmental'
            )

            if is_new:
                stats['new_barriers'] += 1
                print(f"      Created new barrier: {barrier_id}")

            # Add disability-barrier relationship
            if barrier_id not in relationships['disability_barriers'][disability_id]:
                relationships['disability_barriers'][disability_id].append(barrier_id)
                stats['disability_barrier_rels'] += 1

            # Initialize accommodation array for this barrier
            if barrier_id not in relationships['barrier_accommodations']:
                relationships['barrier_accommodations'][barrier_id] = []

            # Process accommodations for this barrier
            for acc_name in accommodation_names:
                acc_name_normalized = normalize_accommodation_name(acc_name)

                if not acc_name_normalized:
                    continue

                # Get or create accommodation
                acc_id, is_new = get_or_create_entity(
                    acc_name_normalized, accommodations, 'Accommodation', 'Workplace'
                )

                if is_new:
                    stats['new_accommodations'] += 1
                    print(f"      Created new accommodation: {acc_id} - {acc_name_normalized}")

                # Add barrier-accommodation relationship
                if acc_id not in relationships['barrier_accommodations'][barrier_id]:
                    relationships['barrier_accommodations'][barrier_id].append(acc_id)
                    stats['barrier_accommodation_rels'] += 1

                # Add disability-accommodation relationship (via barrier)
                if acc_id not in relationships['disability_accommodations'][disability_id]:
                    relationships['disability_accommodations'][disability_id].append(acc_id)
                    stats['disability_accommodation_rels'] += 1

    # Save updated data
    print("\n" + "="*60)
    print("Saving updated data files...")
    print("="*60)

    save_json('/home/user/accommodation-finder/disabilities.json', disabilities)
    save_json('/home/user/accommodation-finder/limitations.json', limitations)
    save_json('/home/user/accommodation-finder/barriers.json', barriers)
    save_json('/home/user/accommodation-finder/accommodations.json', accommodations)
    save_json('/home/user/accommodation-finder/relationships.json', relationships)

    print("\nFinal Statistics:")
    print(f"  Total disabilities: {len(disabilities)}")
    print(f"  Total limitations: {len(limitations)} (+{stats['new_limitations']} new)")
    print(f"  Total barriers: {len(barriers)} (+{stats['new_barriers']} new)")
    print(f"  Total accommodations: {len(accommodations)} (+{stats['new_accommodations']} new)")
    print(f"\nRelationships created:")
    print(f"  Disability -> Limitation: {stats['disability_limitation_rels']}")
    print(f"  Disability -> Barrier: {stats['disability_barrier_rels']}")
    print(f"  Limitation -> Accommodation: {stats['limitation_accommodation_rels']}")
    print(f"  Barrier -> Accommodation: {stats['barrier_accommodation_rels']}")
    print(f"  Disability -> Accommodation: {stats['disability_accommodation_rels']}")

    print("\n✓ All data files updated successfully!")

if __name__ == '__main__':
    main()
