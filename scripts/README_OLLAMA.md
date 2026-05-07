#!/usr/bin/env python3
"""
USAGE — ollama_generator.py (Unified Entry Point)

═══════════════════════════════════════════════════════════════════════════════

TWO FILES ONLY:
  ✅ scripts/ollama_client.py       — HTTP client for Ollama
  ✅ scripts/ollama_generator.py    — Main entry point + analysis engine

═══════════════════════════════════════════════════════════════════════════════

QUICK START

# List available projects
$ python scripts/ollama_generator.py --list

# Run analysis (first project, default settings)
$ python scripts/ollama_generator.py

# Specific project
$ python scripts/ollama_generator.py Americas

# With custom model
$ python scripts/ollama_generator.py Americas qwen2:14b

# Full control (project + model + temperature + max_tokens)
$ python scripts/ollama_generator.py Americas phi3:14b 0.1 2000

═══════════════════════════════════════════════════════════════════════════════

PARAMETERS

python scripts/ollama_generator.py [project] [model] [temperature] [max_tokens]

  project         — Project name (partial match, leave empty for first)
                    Use "--list" to see available projects
                    
  model           — Ollama model (phi3:14b, qwen2:14b, mistral, etc.)
                    Default: phi3:14b (set in ollama_client.py)
                    Must pull first: ollama pull <model>
                    
  temperature     — 0.0-1.0 (higher = more creative)
                    0.0 = deterministic (always same)
                    0.1 = consistent, deterministic (RECOMMENDED)
                    0.5 = balanced
                    1.0 = maximum randomness
                    Default: 0.1
                    
  max_tokens      — Max response length (reserved for future use)
                    Default: 2000

═══════════════════════════════════════════════════════════════════════════════

ENVIRONMENT VARIABLES (Alternative to command line)

export OLLAMA_MODEL="phi3:14b"
export OLLAMA_TEMP="0.1"
export OLLAMA_TOKENS="2000"

Then just run: python scripts/ollama_generator.py

═══════════════════════════════════════════════════════════════════════════════

EXAMPLES

# Deterministic (same output every time)
$ python scripts/ollama_generator.py Americas phi3:14b 0.0

# Quick analysis with fast model
$ python scripts/ollama_generator.py Americas phi3:3.8b 0.1

# Complex analysis with high-quality model
$ python scripts/ollama_generator.py Americas qwen2:14b 0.5

# First project, all defaults
$ python scripts/ollama_generator.py

═══════════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING

Problem: "Connection refused" or "Cannot connect to Ollama"
  $ ollama serve              # Start Ollama server
  $ ollama pull phi3:14b      # Download model
  $ python scripts/ollama_generator.py Americas

Problem: Model not found
  $ ollama pull <model_name>
  # e.g., ollama pull qwen2:14b

Problem: Analysis is slow
  • Use faster model: phi3:3.8b
  • Lower temperature: 0.1 (faster than 0.5 or 1.0)
  • Check: ollama ps

═══════════════════════════════════════════════════════════════════════════════

MODEL RECOMMENDATIONS

Fast (1-2 min):          phi3:3.8b, qwen2:7b
Balanced (2-3 min):      phi3:14b (RECOMMENDED), qwen2:14b, mistral
Deep/Slow (3-5 min):     llama2:13b

═══════════════════════════════════════════════════════════════════════════════

FILES & ARCHITECTURE

scripts/ollama_generator.py
  └─ Auto-detects project paths
  └─ Parses command-line arguments
  └─ Loads JSON data
  └─ Computes metrics
  └─ Generates 4 reports (parallel)
  └─ Saves markdown files

         ↓

scripts/ollama_client.py
  └─ HTTP client for Ollama API
  └─ Streaming responses
  └─ Error handling + retries
  └─ Connection checking

         ↓

Local Ollama Server (http://localhost:11434)
  └─ LLM Model (phi3, qwen, mistral, etc)

═══════════════════════════════════════════════════════════════════════════════

OUTPUT

Generated in: ai_analysis_output/

  01_EDA_REPORT.md              — Model structure, unused assets
  02_DAX_OPTIMIZATION.md        — Measure complexity, refactoring
  03_PERFORMANCE_ANALYSIS.md    — Bottlenecks, hub tables
  04_DATA_QUALITY.md            — Column usage, cleanup recommendations

Each is a standalone markdown file with AI-generated insights.

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(__doc__)
