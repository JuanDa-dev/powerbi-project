#!/usr/bin/env python3
"""
Quick Start Guide - Interactive Script
Helps users get started quickly
"""

import os
import sys
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_section(title):
    """Print formatted section"""
    print(f"\n► {title}")
    print("-" * 40)

def main():
    """Interactive quick start"""
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print_header("🚀 POWER BI EDA TOOL - QUICK START")
    
    print("""
¡Bienvenido! Este script te ayuda a empezar rápidamente.

Tienes varias opciones para analizar tus proyectos Power BI:
    """)
    
    print_section("📋 OPCIÓN 1: Analizar un Proyecto Específico (RECOMENDADO)")
    print("""
Comando:
    python main.py ../RecursosFuente/CorporateSpend.pbip

Cuándo usar:
    - Cuando sabes exactamente qué proyecto quieres analizar
    - Quieres máxima claridad y control

Ventajas:
    ✓ Rápido y directo
    ✓ No hay menú interactivo
    ✓ Fácil de automatizar
    """)
    
    print_section("📋 OPCIÓN 2: Seleccionar Interactivamente")
    print("""
Comando:
    python analyze_pbip.py ../RecursosFuente

Cuándo usar:
    - No recuerdas el nombre exacto del proyecto
    - Hay múltiples proyectos y quieres elegir

Ventajas:
    ✓ Interfaz amigable con menú
    ✓ Auto-detecta proyectos válidos
    ✓ Valida estructura antes de analizar
    """)
    
    print_section("📋 OPCIÓN 3: Analizar Todos los Proyectos")
    print("""
Comando:
    python analyze_pbip.py ../RecursosFuente --all

Cuándo usar:
    - Quieres analizar todos los proyectos de una vez
    - Necesitas reportes de múltiples proyectos

Ventajas:
    ✓ Procesa todos automáticamente
    ✓ Genera reportes para cada proyecto
    ✓ Resumen de resultados
    """)
    
    print_section("📋 OPCIÓN 4: Descubrimiento Automático")
    print("""
Comando:
    python run.py

Cuándo usar:
    - Prefieres que el sistema encuentre todo automáticamente
    - Quieres una experiencia más automática

Ventajas:
    ✓ Máxima automatización
    ✓ Sin necesidad de recordar rutas
    ✓ Interfaz simplificada
    """)
    
    print_section("🧪 OPCIÓN 5: Diagnosticar Problemas")
    print("""
Si algo no funciona, ejecuta:
    python test_pbip.py ../RecursosFuente/CorporateSpend.pbip

Este script muestra:
    ✓ Si los archivos existen
    ✓ Si las carpetas asociadas están en el lugar correcto
    ✓ Información detallada para debugging
    ✓ Mensajes de error específicos
    """)
    
    print_section("📚 DOCUMENTACIÓN DISPONIBLE")
    print("""
Archivos de referencia rápida:
    1. GUIA_RAPIDA_USO.md
       → Guía de 5 minutos con todos los comandos
    
    2. SOLUCION_ERROR_NO_MODEL.md
       → Si recibes error "No model found"
    
    3. TROUBLESHOOTING.md
       → Solución de problemas comunes
    
    4. INDICE_DOCUMENTACION.md
       → Índice completo de documentación
    """)
    
    print_section("⚡ PRIMEROS PASOS")
    print("""
1. Abre una terminal
2. Ve a la carpeta pbi-mcp-enhanced:
       cd pbi-mcp-enhanced
    
3. Ejecuta uno de estos comandos:
    
    # RECOMENDADO - Específico
    python main.py ../RecursosFuente/CorporateSpend.pbip
    
    # ALTERNATIVA - Interactivo
    python analyze_pbip.py ../RecursosFuente
    
    # ALTERNATIVA - Todos
    python analyze_pbip.py ../RecursosFuente --all

4. Los reportes se generarán en: output/

5. Abre los reportes .md con cualquier editor de texto
    """)
    
    print_section("❓ ¿QUÉ PUEDO ANALIZAR?")
    print("""
El tool analiza automáticamente:
    
    📊 ESTRUCTURA DEL MODELO
       - Tablas (Fact, Dimension, Calculated)
       - Medidas (DAX, Complejidad)
       - Columnas y Data Types
    
    🔗 RELACIONES
       - Mapeo completo
       - Análisis de conectividad
       - Detección de problemas
    
    ⚙️ REGLAS DE BEST PRACTICE
       - 15 reglas pre-configuradas
       - Scoring automático (0-100)
       - Recomendaciones
    
    📈 VISUALIZACIONES
       - Diagramas de relaciones
       - Gráficos de complejidad
       - Distribución de tipos
    """)
    
    print_section("💡 TIPS IMPORTANTES")
    print("""
    💡 Los comandos deben ejecutarse desde pbi-mcp-enhanced/
    
    💡 Si obtienes error "No model found":
       → Lee: SOLUCION_ERROR_NO_MODEL.md
       → Ejecuta: python test_pbip.py <ruta>
    
    💡 Asegúrate de instalar dependencias:
       → pip install -r requirements.txt
    
    💡 Usa -v para ver más detalles:
       → python main.py <ruta> -v
    
    💡 Los reportes son archivos Markdown (.md)
       → Puedes verlos en VS Code, GitHub, etc.
    """)
    
    print_header("🎯 PRÓXIMO PASO")
    print("""
    Elige tu opción arriba y ejecuta el comando.
    
    Si necesitas ayuda, abre:
    → GUIA_RAPIDA_USO.md
    → TROUBLESHOOTING.md
    
    ¡Listo para comenzar! 🚀
    """)

if __name__ == "__main__":
    main()
    input("\nPresiona ENTER para terminar...")
