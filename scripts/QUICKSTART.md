# Quick Start - AI-Enhanced Documentation

## Setup (First Time Only)

### 1. Install Ollama
Download from https://ollama.ai

### 2. Pull the Model
```bash
ollama pull llama3.1
```

### 3. Start Ollama Server
```bash
ollama serve
```
Keep this terminal open. Ollama will listen on `http://localhost:11434`

## Usage

### Verify Connection
```bash
cd scripts
python ollama_client.py
```

Expected output:
```
✅ Ollama connection OK

📝 Response:
Power BI is a business intelligence and data visualization...
```

### Generate AI Documentation

From the `/powerbi-project` root:

```bash
python scripts/ollama_generator.py
```

This will:
1. Classify tables (FACT, DIMENSION, etc.)
2. Describe measures with aggregation types
3. Generate markdown documentation

**Output files:**
- `powerbi-project/output_ai/tables_enriched.json` - Tables with AI annotations
- `powerbi-project/output_ai/AI_DOCUMENTATION.md` - Generated documentation

### Example: Custom Paths

```bash
python scripts/ollama_generator.py \
  powerbi-project/data/tables.json \
  powerbi-project/data/relationships.json \
  powerbi-project/data/pages.json \
  powerbi-project/output_ai
```

## What the AI Does

### Table Classification
Analyzes table structure to determine:
- **FACT**: Many measures, numeric columns, has foreign keys
- **DIMENSION**: Text/keys, few measures, referenced by facts
- **BRIDGE**: Connects many-to-many relationships
- **CALCULATION**: Pure DAX, no source columns
- **PARAMETER**: Fixed values or date ranges

### Measure Analysis
For each measure, the AI determines:
- **Description**: What the measure calculates
- **Type**: SUM, COUNT, RATIO, TIME_INTELLIGENCE, DYNAMIC, CONDITIONAL, FILTER
- **Stub status**: Whether measure is fully implemented

### Documentation Generation
Creates sections:
1. Executive Summary
2. Data Model Overview
3. Table Specifications
4. Measure Dictionary
5. Key Relationships
6. Data Quality Notes

## Troubleshooting

### "Cannot connect to Ollama"
Make sure `ollama serve` is running in another terminal.

### "Model not found"
Run `ollama pull llama3.1`

### Slow performance
First generation takes ~30-60 seconds (model loading).
Subsequent runs are faster (~20-40 seconds).

### Out of memory
Free up RAM or use `ollama pull llama2` (smaller model, uses ~3.5GB)

## Performance Tips

- **Lower temperature = faster**: Already set to 0.1 for documentation
- **Shorter prompts = faster**: System automatically truncates long expressions
- **Batch operations**: Generate all at once rather than incrementally
- **Model size**: llama3.1 (11B) vs llama2 (7B) - smaller is faster

## What's Next?

1. ✅ Verify tables are correctly classified
2. ✅ Review measure types
3. 📝 Customize `AI_DOCUMENTATION.md` with your insights
4. 🔄 Export to PDF or Confluence
5. 📊 Use enriched JSON for downstream processing

## More Info

See `scripts/README.md` for complete documentation.
