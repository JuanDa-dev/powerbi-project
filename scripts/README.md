# Scripts Directory

Utility scripts for Power BI semantic model analysis and AI-enhanced documentation.

## Structure

```
scripts/
├── __init__.py                    # Package marker
├── ollama_client.py              # HTTP client for local Ollama
├── ollama_generator.py           # AI documentation generator
├── check_types.py                # Verify datatype extraction
├── check_classification.py       # Verify AI classifications
├── inspect_tmdl.py              # Inspect TMDL file structure
└── README.md                     # This file
```

## Ollama Integration

### Prerequisites

1. **Install Ollama**: https://ollama.ai
2. **Pull llama3.1 model**:
   ```bash
   ollama pull llama3.1
   ```
3. **Start Ollama server**:
   ```bash
   ollama serve
   ```
   This starts HTTP server on `http://localhost:11434`

### Usage

#### 1. Test Connection

```bash
python scripts/ollama_client.py
```

Output:
```
✅ Ollama connection OK

📝 Response:
Power BI is a business intelligence and data visualization tool...
```

#### 2. Generate AI-Enriched Documentation

```bash
cd scripts
python ollama_generator.py
```

Or with custom paths:
```bash
python ollama_generator.py \
  ../powerbi-project/data/tables.json \
  ../powerbi-project/data/relationships.json \
  ../powerbi-project/data/pages.json \
  ../powerbi-project/output_ai
```

This will:
- ✅ Classify tables (FACT, DIMENSION, BRIDGE, CALCULATION, PARAMETER)
- ✅ Describe measures with aggregation types
- ✅ Generate markdown documentation
- ✅ Save enriched JSON with AI annotations

### Output

- `tables_enriched.json` - Tables with AI classifications and reasoning
- `AI_DOCUMENTATION.md` - AI-generated technical documentation

### Supported Models

The scripts default to `llama3.1` but support any Ollama model:

```bash
# Available models
ollama list

# Use alternative model
python ollama_generator.py  # Uses llama3.1 by default
```

## Data Type Verification

### Check Column Datatypes

```bash
python scripts/check_types.py
```

Shows detected types:
```
Unique dataTypes found: ['dateTime', 'double', 'int64', 'string']

Sample columns by type:
  Date: dateTime
  amt_total: double
  qty_documents: int64
  supplier_name: string
```

### Check Type Classifications

```bash
python scripts/check_classification.py
```

Shows classified types:
```
Datatype Distribution (Classified):
  Text: 118
  Calculated Column: 11
  Decimal Number: 10
  DateTime: 3
  Date: 2
  Whole Number: 1
```

### Inspect TMDL Structure

```bash
python scripts/inspect_tmdl.py
```

Visualizes TMDL formatting with tabs and spaces visible.

## Integration with Main Pipeline

The main pipeline (`main.py`) uses the parsers and visualizers directly.
The scripts in this directory are optional enhancements:

1. **Core pipeline** (always runs):
   ```bash
   python main.py ../RecursosFuente/OnlineBaseline.pbip
   ```

2. **Optional AI enhancement** (requires Ollama):
   ```bash
   python scripts/ollama_generator.py
   ```

## Environment Variables

Override defaults with environment variables:

```bash
# Custom Ollama URL
export OLLAMA_BASE_URL=http://remote-machine:11434

# Custom model
export OLLAMA_MODEL=llama2

# Request timeout (seconds)
export OLLAMA_TIMEOUT=600
```

## Troubleshooting

### "Cannot connect to Ollama"

```
❌ Cannot reach Ollama at http://localhost:11434
   Start Ollama with: ollama serve
```

**Solution**: Ensure Ollama is running
```bash
ollama serve
```

### "Model not found"

```
⚠️  Model 'llama3.1' not found in Ollama
   Available models: llama2, qwen
```

**Solution**: Pull the model
```bash
ollama pull llama3.1
```

### Request timeout

```
Ollama request timed out after 300s
```

**Solution**: Use shorter prompts or increase timeout in `ollama_client.py`

### Out of memory

```
llama3.1 loaded with out of memory error
```

**Solution**: Free up RAM or use smaller model
```bash
ollama pull llama2  # Smaller model
```

## Performance Notes

- **First generation**: ~30-60 seconds (model loading + context processing)
- **Subsequent runs**: ~20-40 seconds (model cached)
- **Temperature 0.1**: Low creativity, deterministic for documentation
- **Context window 8192**: Supports moderate-sized models

## Dependencies

- `httpx` - HTTP client for Ollama API
- `json` - Built-in, for JSON parsing
- `pathlib` - Built-in, for file operations

No external ML dependencies needed—Ollama handles all inference.

## Development

To add new AI-powered scripts:

1. Import `ollama_client.generate()` function
2. Define system prompts
3. Use `check_connection()` before generating
4. Parse responses as JSON for reliability

Example:
```python
from ollama_client import generate, check_connection

if check_connection():
    response = generate(
        prompt="Your prompt here",
        system="System context",
        temperature=0.1
    )
    print(response)
```

## License

Part of powerbi-project suite.
