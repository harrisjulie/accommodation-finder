#!/usr/bin/env python3
"""
Generate barrier_accommodations and function_accommodations mappings
based on keyword matching and logical inference from existing data.
"""

import json
import re
from collections import defaultdict

# Load existing data
with open('accommodations.json', 'r') as f:
    accommodations = json.load(f)

with open('barriers.json', 'r') as f:
    barriers = json.load(f)

with open('functions.json', 'r') as f:
    functions = json.load(f)

with open('relationships.json', 'r') as f:
    relationships = json.load(f)

print("Generating barrier_accommodations and function_accommodations...")

# Helper function to extract keywords
def get_keywords(text):
    """Extract meaningful keywords from text"""
    text = text.lower()
    # Remove common words
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    words = re.findall(r'\b\w+\b', text)
    return [w for w in words if w not in stopwords and len(w) > 2]

# Helper function to calculate keyword overlap
def keyword_match_score(keywords1, keywords2):
    """Calculate how many keywords match between two sets"""
    set1 = set(keywords1)
    set2 = set(keywords2)
    if not set1 or not set2:
        return 0
    return len(set1 & set2)

# ============================================================================
# Generate BARRIER -> ACCOMMODATIONS mappings
# ============================================================================

barrier_accommodations = defaultdict(list)

for barrier in barriers:
    barrier_keywords = get_keywords(barrier['name'] + ' ' + barrier.get('description', ''))
    matches = []

    for acc in accommodations:
        acc_keywords = get_keywords(acc['name'] + ' ' + acc.get('description', ''))
        score = keyword_match_score(barrier_keywords, acc_keywords)

        # Also check category matching
        if barrier.get('category') and acc.get('category'):
            if 'physical' in barrier.get('category', '').lower() and 'physical' in acc.get('category', '').lower():
                score += 2
            if 'sensory' in barrier.get('category', '').lower() and 'environment' in acc.get('category', '').lower():
                score += 2
            if 'communication' in barrier.get('category', '').lower() and 'communication' in acc.get('category', '').lower():
                score += 2

        # Specific barrier-accommodation mappings based on common patterns
        barrier_name_lower = barrier['name'].lower()
        acc_name_lower = acc['name'].lower()

        # Physical barriers
        if 'stair' in barrier_name_lower or 'step' in barrier_name_lower:
            if 'ramp' in acc_name_lower or 'elevator' in acc_name_lower or 'accessible' in acc_name_lower or 'ground floor' in acc_name_lower:
                score += 5

        # Noise barriers
        if 'noise' in barrier_name_lower or 'loud' in barrier_name_lower:
            if 'quiet' in acc_name_lower or 'noise' in acc_name_lower or 'headphone' in acc_name_lower or 'private' in acc_name_lower:
                score += 5

        # Lighting barriers
        if 'light' in barrier_name_lower or 'bright' in barrier_name_lower or 'glare' in barrier_name_lower:
            if 'light' in acc_name_lower or 'shade' in acc_name_lower or 'lamp' in acc_name_lower or 'blind' in acc_name_lower:
                score += 5

        # Temperature barriers
        if 'temperature' in barrier_name_lower or 'hot' in barrier_name_lower or 'cold' in barrier_name_lower:
            if 'temperature' in acc_name_lower or 'fan' in acc_name_lower or 'heater' in acc_name_lower or 'climate' in acc_name_lower:
                score += 5

        # Distance/mobility barriers
        if 'distance' in barrier_name_lower or 'parking' in barrier_name_lower or 'walking' in barrier_name_lower:
            if 'parking' in acc_name_lower or 'remote' in acc_name_lower or 'telecommute' in acc_name_lower or 'workstation' in acc_name_lower:
                score += 5

        # Schedule barriers
        if 'schedule' in barrier_name_lower or 'deadline' in barrier_name_lower or 'pace' in barrier_name_lower:
            if 'flexible' in acc_name_lower or 'schedule' in acc_name_lower or 'break' in acc_name_lower or 'deadline' in acc_name_lower:
                score += 5

        # Communication barriers
        if 'communication' in barrier_name_lower or 'speaking' in barrier_name_lower or 'hearing' in barrier_name_lower:
            if 'interpreter' in acc_name_lower or 'amplif' in acc_name_lower or 'written' in acc_name_lower or 'email' in acc_name_lower or 'text' in acc_name_lower:
                score += 5

        if score > 0:
            matches.append((acc['id'], score))

    # Sort by score and take top matches
    matches.sort(key=lambda x: x[1], reverse=True)

    # Take accommodations with score >= 2, or top 10 if none meet that threshold
    top_matches = [aid for aid, score in matches if score >= 2]
    if not top_matches and matches:
        top_matches = [aid for aid, score in matches[:10]]

    if top_matches:
        barrier_accommodations[barrier['id']] = top_matches
        print(f"  {barrier['id']} ({barrier['name']}): {len(top_matches)} accommodations")

# ============================================================================
# Generate FUNCTION -> ACCOMMODATIONS mappings
# ============================================================================

function_accommodations = defaultdict(list)

for func in functions:
    func_keywords = get_keywords(func['name'] + ' ' + func.get('description', ''))
    matches = []

    for acc in accommodations:
        acc_keywords = get_keywords(acc['name'] + ' ' + acc.get('description', ''))
        score = keyword_match_score(func_keywords, acc_keywords)

        # Specific function-accommodation mappings
        func_name_lower = func['name'].lower()
        acc_name_lower = acc['name'].lower()

        # Phone/communication functions
        if 'phone' in func_name_lower or 'call' in func_name_lower:
            if 'phone' in acc_name_lower or 'headset' in acc_name_lower or 'amplif' in acc_name_lower or 'tty' in acc_name_lower or 'relay' in acc_name_lower:
                score += 5

        # Meeting functions
        if 'meeting' in func_name_lower or 'conferenc' in func_name_lower:
            if 'meeting' in acc_name_lower or 'agenda' in acc_name_lower or 'notes' in acc_name_lower or 'quiet' in acc_name_lower or 'interpreter' in acc_name_lower:
                score += 5

        # Computer work functions
        if 'computer' in func_name_lower or 'typing' in func_name_lower or 'keyboard' in func_name_lower:
            if 'keyboard' in acc_name_lower or 'mouse' in acc_name_lower or 'screen' in acc_name_lower or 'voice' in acc_name_lower or 'software' in acc_name_lower or 'ergonomic' in acc_name_lower:
                score += 5

        # Reading/writing functions
        if 'read' in func_name_lower or 'writ' in func_name_lower or 'document' in func_name_lower:
            if 'screen reader' in acc_name_lower or 'magnif' in acc_name_lower or 'speech' in acc_name_lower or 'dictation' in acc_name_lower or 'large' in acc_name_lower:
                score += 5

        # Travel functions
        if 'travel' in func_name_lower or 'driving' in func_name_lower or 'commut' in func_name_lower:
            if 'parking' in acc_name_lower or 'remote' in acc_name_lower or 'telecommute' in acc_name_lower or 'flexible' in acc_name_lower or 'schedule' in acc_name_lower:
                score += 5

        # Lifting/physical functions
        if 'lift' in func_name_lower or 'carry' in func_name_lower or 'physical' in func_name_lower:
            if 'cart' in acc_name_lower or 'dolly' in acc_name_lower or 'ergonomic' in acc_name_lower or 'assist' in acc_name_lower or 'modify' in acc_name_lower:
                score += 5

        # Standing/sitting functions
        if 'stand' in func_name_lower or 'sit' in func_name_lower:
            if 'chair' in acc_name_lower or 'stool' in acc_name_lower or 'desk' in acc_name_lower or 'break' in acc_name_lower or 'rest' in acc_name_lower:
                score += 5

        # Concentration/focus functions
        if 'concentrat' in func_name_lower or 'focus' in func_name_lower or 'attention' in func_name_lower:
            if 'quiet' in acc_name_lower or 'distraction' in acc_name_lower or 'private' in acc_name_lower or 'break' in acc_name_lower or 'reminder' in acc_name_lower:
                score += 5

        # Time management functions
        if 'deadline' in func_name_lower or 'schedul' in func_name_lower or 'time' in func_name_lower:
            if 'flexible' in acc_name_lower or 'schedule' in acc_name_lower or 'deadline' in acc_name_lower or 'reminder' in acc_name_lower or 'planner' in acc_name_lower:
                score += 5

        if score > 0:
            matches.append((acc['id'], score))

    # Sort by score and take top matches
    matches.sort(key=lambda x: x[1], reverse=True)

    # Take accommodations with score >= 2, or top 10 if none meet that threshold
    top_matches = [aid for aid, score in matches if score >= 2]
    if not top_matches and matches:
        top_matches = [aid for aid, score in matches[:10]]

    if top_matches:
        function_accommodations[func['id']] = top_matches
        print(f"  {func['id']} ({func['name']}): {len(top_matches)} accommodations")

# ============================================================================
# Update relationships.json
# ============================================================================

relationships['barrier_accommodations'] = dict(barrier_accommodations)
relationships['function_accommodations'] = dict(function_accommodations)

print(f"\nGenerated:")
print(f"  - {len(barrier_accommodations)} barrier -> accommodation mappings")
print(f"  - {len(function_accommodations)} function -> accommodation mappings")

# Save updated relationships
with open('relationships.json', 'w') as f:
    json.dump(relationships, f, indent=2)

print(f"\n✅ Updated relationships.json successfully!")
