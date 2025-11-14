#!/usr/bin/env python3
"""
Parse the Disability Database Info Total.txt document to extract:
- All disabilities
- Limitations for each disability
- Barriers (work-related functions) for each disability
- Accommodations for each limitation and barrier
"""

import json
import re
from collections import defaultdict

def parse_document(filepath):
    """Parse the main disability document."""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by disability sections (look for "About [Disability]")
    disability_sections = re.split(r'\nAbout ', content)

    disabilities_data = {}

    for section in disability_sections[1:]:  # Skip first empty section
        lines = section.strip().split('\n')
        if not lines:
            continue

        # First line is the disability name
        disability_name = lines[0].strip()

        # Find "By Limitation" and "By Work-Related Function" sections
        section_text = '\n'.join(lines)

        limitations = {}
        barriers = {}

        # Parse limitations section
        by_limitation_match = re.search(r'By Limitation\n(.*?)(?=By Work-Related Function|$)',
                                       section_text, re.DOTALL)
        if by_limitation_match:
            limitations_text = by_limitation_match.group(1)
            limitations = parse_items_and_accommodations(limitations_text)

        # Parse barriers/functions section
        by_function_match = re.search(r'By Work-Related Function\n(.*?)(?=\nAbout |$)',
                                     section_text, re.DOTALL)
        if by_function_match:
            functions_text = by_function_match.group(1)
            barriers = parse_items_and_accommodations(functions_text)

        if limitations or barriers:
            disabilities_data[disability_name] = {
                'limitations': limitations,
                'barriers': barriers
            }

    return disabilities_data

def parse_items_and_accommodations(text):
    """Parse limitation/barrier items and their accommodations."""
    items = {}

    # Split into individual items (they start at the beginning of a line, not indented)
    lines = text.strip().split('\n')
    current_item = None
    current_accommodations = []

    for line in lines:
        # Check if this is a new item (not indented with *, not empty)
        if line and not line.startswith(' ') and not line.startswith('*') and not line.startswith('\t'):
            # Save previous item if exists
            if current_item:
                items[current_item] = current_accommodations

            # Start new item
            current_item = line.strip()
            current_accommodations = []

        # If line starts with * and we have a current item, it's an accommodation
        elif line.strip().startswith('*') and current_item:
            accommodation = line.strip().lstrip('*').strip()
            if accommodation:
                current_accommodations.append(accommodation)

    # Save last item
    if current_item:
        items[current_item] = current_accommodations

    return items

def main():
    print("Parsing Disability Database Info Total.txt...")

    disabilities_data = parse_document('/home/user/accommodation-finder/Disability Database Info Total.txt')

    print(f"\nFound {len(disabilities_data)} disabilities")

    # Output summary
    total_limitations = 0
    total_barriers = 0

    for disability, data in disabilities_data.items():
        num_limitations = len(data['limitations'])
        num_barriers = len(data['barriers'])
        total_limitations += num_limitations
        total_barriers += num_barriers

        print(f"\n{disability}:")
        print(f"  Limitations: {num_limitations}")
        print(f"  Barriers: {num_barriers}")

        if num_limitations > 0:
            print(f"  Sample limitations: {list(data['limitations'].keys())[:3]}")
        if num_barriers > 0:
            print(f"  Sample barriers: {list(data['barriers'].keys())[:3]}")

    print(f"\nTotal limitations across all disabilities: {total_limitations}")
    print(f"Total barriers across all disabilities: {total_barriers}")

    # Save parsed data
    with open('/home/user/accommodation-finder/parsed_disabilities.json', 'w') as f:
        json.dump(disabilities_data, f, indent=2)

    print("\nParsed data saved to parsed_disabilities.json")

if __name__ == '__main__':
    main()
