
import json

# Load all files
with open('data/accommodations.json') as f:
    accommodations = json.load(f)
with open('data/disabilities.json') as f:
    disabilities = json.load(f)
with open('data/relationships.json') as f:
    relationships = json.load(f)

# Validation checks
print("RELATIONSHIP VALIDATION REPORT")
print("=" * 40)

# Check disability coverage
covered_disabilities = len(relationships.get('disability_accommodations', {}))
total_disabilities = len(disabilities)
print(f"Disabilities with accommodations: {covered_disabilities}/{total_disabilities}")

# Check each disability has at least 5 accommodations
for d in disabilities:
    acc_count = len(relationships.get('disability_accommodations', {}).get(d['id'], []))
    if acc_count < 5:
        print(f"  WARNING: {d['id']} ({d['name']}) has only {acc_count} accommodations")

# Check accommodations are used
all_acc_ids = set()
for mapping in relationships.get('disability_accommodations', {}).values():
    all_acc_ids.update(mapping)

unused = []
for acc in accommodations:
    if acc['id'] not in all_acc_ids:
        unused.append(acc['id'])

if unused:
    print(f"\nUnused accommodations: {len(unused)}")
    print(f"  IDs: {', '.join(unused[:10])}...")

print("\nValidation complete!")
