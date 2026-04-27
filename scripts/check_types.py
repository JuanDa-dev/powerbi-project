import json
with open('powerbi-project/data/tables.json') as f:
    tables = json.load(f)
    
# Get all unique datatypes
datatypes = set()
for table in tables:
    for col in table.get('columns', []):
        datatypes.add(col.get('dataType', 'Unknown'))

print('Unique dataTypes found:', sorted(datatypes))
print()

# Sample columns from different types
print('Sample columns by type:')
seen_types = set()
for table in tables:
    for col in table.get('columns', []):
        dt = col.get('dataType')
        if dt and dt not in seen_types:
            print(f"  {col['name']}: {dt}")
            seen_types.add(dt)
