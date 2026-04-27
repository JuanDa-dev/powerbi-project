import json
from visualizers.datatype_distribution import DatatypeDistributionBuilder

# Load and classify
viz = DatatypeDistributionBuilder('powerbi-project/data/tables.json')
distribution = viz._extract_datatype_distribution()

print("Datatype Distribution (Classified):")
for dtype, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
    print(f"  {dtype}: {count}")
