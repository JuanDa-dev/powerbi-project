# Read a table file and print first 80 lines to understand structure
with open('../RecursosFuente/OnlineBaseline.SemanticModel/definition/tables/fact_spend_transactions.tmdl', 'r') as f:
    lines = f.readlines()[:80]
    for i, line in enumerate(lines, 1):
        # Show spaces/tabs explicitly
        display = line.replace('\t', '→').replace(' ', '·')
        print(f"{i:3d}: {display.rstrip()}")
