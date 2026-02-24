# AMC - Herramienta de Análisis Multicriterio

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.30+-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-IDOM-green.svg" alt="License">
</p>

Dashboard interactivo para **Análisis de Decisión Multicriterio (MCDA)** que permite evaluar y comparar múltiples alternativas usando criterios ponderados organizados jerárquicamente.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Métodos de Análisis](#-métodos-de-análisis)
- [Guía de Páginas](#-guía-de-páginas)
- [Formato del Excel](#-formato-del-excel)
- [Flujo de Trabajo Recomendado](#-flujo-de-trabajo-recomendado)
- [Soporte](#-soporte)

---

## ✨ Características

| Funcionalidad | Descripción |
|---------------|-------------|
| **3 Métodos MCDA** | Suma Ponderada, TOPSIS y ELECTRE I |
| **5 Normalizaciones** | Min-Max, Z-Score, Máximo, Suma, Vectorial |
| **AHP Integrado** | Verificación automática de consistencia (CR) |
| **13 Visualizaciones** | Radar, Heatmap, Waterfall, Tornado, etc. |
| **Análisis de Sensibilidad** | One-at-a-Time (OAT) y Monte Carlo |
| **Exportación** | Reportes en PDF y Excel |
| **Interfaz Web** | Dashboard interactivo con Streamlit |

---

## 💻 Requisitos

- **Python 3.7+**
- **Navegador web** (Chrome, Firefox, Edge, Safari)

### Dependencias

```
streamlit>=1.30.0
plotly>=5.18.0
openpyxl>=3.1.2
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.11.0
reportlab>=4.0.0
kaleido>=0.2.1
```

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://idom-cea.ghe.com/IDOM-Mobility-Transport/AMC.git
cd AMC
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## ▶️ Uso Rápido

### Iniciar la aplicación

```bash
streamlit run app/main.py
```

La aplicación se abrirá automáticamente en: **http://localhost:8501**

### Crear un Excel modelo (opcional)

Si necesitas generar un archivo Excel de ejemplo con la estructura correcta:

```bash
python crear_modelo.py
```

Esto genera `AMC_Modelo.xlsx` con datos de ejemplo listos para usar.

---

## 📁 Estructura del Proyecto

```
AMC/
│
├── README.md                     # Este archivo
├── requirements.txt              # Dependencias Python
├── crear_modelo.py               # Script para generar Excel modelo
├── GUIA_AMC.md                   # Guía de usuario detallada
├── AMC_Modelo.xlsx               # Excel modelo de ejemplo
│
└── app/                          # Código fuente
    ├── __init__.py
    ├── main.py                   # Dashboard Streamlit (punto de entrada)
    ├── data_loader.py            # Carga datos del Excel
    ├── ahp.py                    # Motor AHP y consistencia
    ├── mcda_methods.py           # Suma Ponderada, TOPSIS, ELECTRE I
    ├── normalization.py          # 5 métodos de normalización
    ├── sensitivity.py            # Sensibilidad OAT y Monte Carlo
    ├── charts.py                 # 13 tipos de gráficos Plotly
    └── report_generator.py       # Generador de reportes PDF
```

### Descripción de Módulos

| Módulo | Función |
|--------|---------|
| `data_loader.py` | Lee el Excel y extrae alternativas, indicadores, pesos y valores |
| `ahp.py` | Calcula pesos AHP y verifica consistencia (CR < 0.10) |
| `normalization.py` | Normaliza valores para hacerlos comparables |
| `mcda_methods.py` | Implementa los 3 métodos de decisión multicriterio |
| `sensitivity.py` | Análisis de robustez con OAT y Monte Carlo |
| `charts.py` | Genera visualizaciones interactivas con Plotly |
| `report_generator.py` | Exporta resultados a PDF |

---

## 📊 Métodos de Análisis

### Métodos MCDA Disponibles

| Método | Descripción | Cuándo Usarlo |
|--------|-------------|---------------|
| **Suma Ponderada** | Promedio ponderado de valores normalizados | Método clásico, fácil de interpretar |
| **TOPSIS** | Distancia a la solución ideal positiva y negativa | Cuando importa la distancia al mejor Y al peor |
| **ELECTRE I** | Relaciones de superación entre alternativas | Cuando hay criterios no compensables |

### Métodos de Normalización

| Método | Fórmula | Uso |
|--------|---------|-----|
| **Min-Max** | (x - min) / (max - min) | El mismo del Excel original |
| **Z-Score** | (x - μ) / σ | Estandarización estadística |
| **Máximo** | x / max | División por el valor máximo |
| **Suma** | x / Σx | División por la suma total |
| **Vectorial** | x / √(Σx²) | Usada internamente por TOPSIS |

---

## 📖 Guía de Páginas

La aplicación tiene **7 páginas** accesibles desde el menú lateral:

### 🏠 1. Inicio
- Carga de archivo Excel
- Resumen del modelo (alternativas, indicadores, visiones)
- Vista previa de la matriz de valores

### ⚖️ 2. Pesos y AHP
- Ajuste interactivo de pesos con sliders
- Matriz de comparación pareada AHP
- Verificación de consistencia (CR)
- Gráfico de dona con distribución de pesos

### 🏆 3. Resultados
- Selección de método de normalización y MCDA
- Cálculo del ranking de alternativas
- Gráfico de barras con scores
- Tabla de resultados ordenada

### 📊 4. Visualizaciones
- **Radar**: Rendimiento por visión
- **Heatmap**: Mapa de calor alternativas vs criterios
- **Barras Apiladas**: Contribución por visión al score
- **Waterfall**: Descomposición del score de una alternativa
- **Coordenadas Paralelas**: Comparación en todos los indicadores

### 🔄 5. Comparación de Métodos
- Ejecuta Suma Ponderada, TOPSIS y ELECTRE simultáneamente
- Gráfico comparativo de rankings
- Correlación de Spearman y Kendall

### 🎲 6. Sensibilidad
- **OAT**: Varía un peso a la vez, gráfico Tornado
- **Monte Carlo**: 1000+ simulaciones aleatorias
- Box plot de distribución de scores
- Histograma de rankings
- Tabla con % de veces en 1er lugar

### 📄 7. Reporte
- Generación de PDF con secciones seleccionables
- Exportación a Excel con múltiples hojas

---

## 📑 Formato del Excel

El archivo Excel debe contener las siguientes hojas:

| Hoja | Contenido |
|------|-----------|
| `ALTERNATIVAS` | Lista de alternativas a evaluar |
| `INDICADORES` | Definición de criterios con tipo (SUMA/RESTA) |
| `VISIONES` | Objetivos estratégicos de alto nivel |
| `VALORES` | Matriz de valores (alternativas × indicadores) |
| `Priorizacion` | Matrices de comparación pareada AHP |

### Estructura Jerárquica

```
VISIONES (8)          ← Objetivos estratégicos de alto nivel
  └── OBJETIVOS (9)   ← Metas específicas dentro de cada visión
       └── INDICADORES (42)  ← Métricas medibles para cada objetivo
```

### Tipos de Indicadores

- **SUMA** (beneficio): Más es mejor (ej: ingresos, calidad)
- **RESTA** (costo): Menos es mejor (ej: costos, tiempo)

---

## 🔄 Flujo de Trabajo Recomendado

```
┌─────────────────────────────────────────────────────┐
│  1. PREPARAR DATOS                                  │
│     Llenar la hoja VALORES del Excel con datos      │
│     reales de cada alternativa                      │
├─────────────────────────────────────────────────────┤
│  2. LANZAR LA APP                                   │
│     streamlit run app/main.py                       │
├─────────────────────────────────────────────────────┤
│  3. VERIFICAR DATOS (Página 1 - Inicio)             │
│     Confirmar que los datos se cargaron bien        │
├─────────────────────────────────────────────────────┤
│  4. AJUSTAR PESOS (Página 2 - Pesos)                │
│     Verificar CR < 0.10                             │
│     Ajustar pesos de visiones si es necesario       │
├─────────────────────────────────────────────────────┤
│  5. CALCULAR RESULTADOS (Página 3)                  │
│     Obtener el ranking con Suma Ponderada           │
├─────────────────────────────────────────────────────┤
│  6. EXPLORAR VISUALMENTE (Página 4)                 │
│     Radar, Heatmap, Waterfall para entender         │
│     por qué gana cada alternativa                   │
├─────────────────────────────────────────────────────┤
│  7. VALIDAR CON OTROS MÉTODOS (Página 5)            │
│     Comparar Suma Ponderada vs TOPSIS vs ELECTRE    │
├─────────────────────────────────────────────────────┤
│  8. VERIFICAR ROBUSTEZ (Página 6)                   │
│     Monte Carlo con 1000 simulaciones               │
│     Tornado para identificar criterios sensibles    │
├─────────────────────────────────────────────────────┤
│  9. GENERAR REPORTE (Página 7)                      │
│     Exportar PDF para presentar resultados          │
└─────────────────────────────────────────────────────┘
```

---

## ❓ Preguntas Frecuentes

**P: Los resultados muestran todo en cero.**  
R: La hoja VALORES del Excel no tiene datos cargados. Ingresa los valores reales de cada alternativa.

**P: El CR sale mayor a 0.10 (inconsistente).**  
R: Revisa las comparaciones pareadas en la hoja Priorización. Si A es 3× más importante que B, y B es 2× más importante que C, entonces A debería ser ~6× más importante que C.

**P: TOPSIS y Suma Ponderada dan rankings diferentes.**  
R: Es normal que difieran ligeramente. Usa Monte Carlo para verificar la robustez de la decisión.

**P: ¿Puedo usar otro archivo Excel?**  
R: Sí, usa el botón "Cargar archivo Excel" en la barra lateral. El archivo debe tener la misma estructura de hojas.

---

## 📞 Soporte

Para dudas o mejoras, contactar al equipo de IDOM Mobility & Transport.

---

## 🛠️ Tecnologías

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly">
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas">
  <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy">
</p>

---

**Desarrollado por IDOM Consulting, Engineering & Architecture**
