# Guia de Usuario - Herramienta AMC (Analisis Multicriterio)

---

## 1. Que es esta herramienta?

La herramienta AMC es un sistema de **Analisis de Decision Multicriterio** que permite evaluar y comparar multiples alternativas (propuestas, proyectos, proveedores, etc.) usando criterios ponderados organizados jerarquicamente.

### Estructura jerarquica del modelo

```
VISIONES (8)          ← Objetivos estrategicos de alto nivel
  └── OBJETIVOS (9)   ← Metas especificas dentro de cada vision
       └── INDICADORES (42)  ← Metricas medibles para cada objetivo
```

**Ejemplo:**
```
V1: Ser escalable
  └── V1.1: Capacidad de crecimiento
       ├── IND01: Numero maximo de usuarios
       ├── IND02: Capacidad de expansion
       └── IND03: Flexibilidad tecnologica
```

### Metodos de analisis disponibles

| Metodo | Descripcion | Cuando usarlo |
|--------|-------------|---------------|
| **Suma Ponderada** | Promedio ponderado de valores normalizados | Metodo clasico, facil de interpretar |
| **TOPSIS** | Distancia a la solucion ideal positiva y negativa | Cuando importa la distancia al mejor Y al peor |
| **ELECTRE I** | Relaciones de superacion entre alternativas | Cuando hay criterios no compensables |

---

## 2. Requisitos previos

### Software necesario
- **Python 3.7+** (incluido con Anaconda)
- **Navegador web** (Chrome, Firefox, Safari, Edge)

### Instalacion de dependencias

Abrir Terminal y ejecutar:

```bash
cd /Users/mateorodriguez/Desktop/AMC
pip install streamlit plotly openpyxl numpy pandas scipy reportlab
```

---

## 3. Como iniciar la aplicacion

### Paso 1: Abrir Terminal

En macOS: Buscar "Terminal" en Spotlight (Cmd + Espacio).

### Paso 2: Navegar a la carpeta del proyecto

```bash
cd /Users/mateorodriguez/Desktop/AMC
```

### Paso 3: Lanzar el dashboard

```bash
streamlit run app/main.py
```

### Paso 4: Abrir en el navegador

Se abrira automaticamente en: **http://localhost:8501**

Si no se abre, copiar esa URL en el navegador manualmente.

### Para detener la aplicacion

Presionar `Ctrl + C` en la Terminal.

---

## 4. Guia pagina por pagina

---

### PAGINA 1: Inicio

**Que hace:** Muestra un resumen general del modelo cargado.

**Pasos:**
1. Al abrir la app, usa el boton **"Cargar archivo Excel"** en la barra lateral izquierda para subir tu archivo (.xlsm/.xlsx).
2. Si necesitas una plantilla de referencia, genera `AMC_Modelo.xlsx` ejecutando `python crear_modelo.py` y cargalo manualmente como cualquier otro archivo.
3. Revisa las metricas principales:
   - Numero de alternativas
   - Numero de indicadores
   - Numero de visiones
   - Escenario actual
4. Desplazate hacia abajo para ver las tablas de alternativas, visiones, indicadores y la matriz de valores.

**Que verificar:**
- Que se muestren todas tus alternativas (Proponente A, B, C, etc.)
- Que los 42 indicadores esten presentes
- Que los valores en la matriz no esten todos en cero (si lo estan, hay que ingresar datos en el Excel)

---

### PAGINA 2: Pesos y AHP

**Que hace:** Permite ajustar los pesos de las visiones y verificar la consistencia de las comparaciones AHP.

#### Pestana "Pesos de Visiones"

1. Cada vision tiene un **slider** que va de 0.0 a 1.0.
2. Mueve los sliders para dar mas o menos importancia a cada vision.
3. Los pesos se **normalizan automaticamente** (siempre suman 1.0).
4. El grafico de dona muestra la distribucion visual de los pesos.

**Ejemplo:**
- Si V1 (Escalabilidad) es muy importante, sube su slider.
- Si V8 (Emergencia) es poco relevante, bajalo.

#### Pestana "Matriz AHP"

1. Muestra la **matriz de comparacion pareada** leida del Excel (hoja Priorizacion).
2. El **gauge de Consistencia (CR)** indica si las comparaciones son logicamente coherentes:
   - **Verde (CR < 0.10):** Consistente. Las comparaciones tienen sentido.
   - **Rojo (CR >= 0.10):** Inconsistente. Hay que revisar las comparaciones en el Excel.
3. Se muestran los pesos derivados matematicamente del AHP.

**Interpretacion del CR:**
- CR = 0.00: Perfectamente consistente
- CR < 0.10: Aceptable
- CR = 0.10 - 0.20: Cuestionable, revisar comparaciones
- CR > 0.20: Inaceptable, las comparaciones se contradicen

#### Pestana "Pesos de Indicadores"

Muestra el peso final de cada indicador, tanto lineal (igual para todos) como ponderado (segun AHP).

---

### PAGINA 3: Resultados

**Que hace:** Calcula y muestra el ranking de alternativas.

**Pasos:**

1. **Seleccionar metodo de normalizacion:**
   - `Min-Max (original)`: El mismo que usa tu Excel. Recomendado.
   - `Z-Score`: Estandarizacion estadistica.
   - `Maximo`: Division por el valor maximo.
   - `Suma`: Division por la suma total.
   - `Vectorial`: Usada internamente por TOPSIS.

2. **Seleccionar metodo MCDA:**
   - `Suma Ponderada`: El metodo original de tu Excel.
   - `TOPSIS`: Metodo de distancia a la solucion ideal.

3. **Clic en "Calcular".**

4. **Interpretar resultados:**
   - El grafico de barras muestra las alternativas ordenadas por score.
   - La tabla muestra score exacto y posicion en el ranking.
   - Un score mas alto = mejor alternativa.

**Nota:** Los pesos usados dependen de lo que seleccionaste en la Pagina 2:
- "Ponderado (AHP)": Usa los pesos del Excel.
- "Lineal (igual)": Todos los indicadores pesan lo mismo.
- "Personalizado (sliders)": Usa los pesos que ajustaste con los sliders.

---

### PAGINA 4: Visualizaciones

**Que hace:** Ofrece 5 tipos de graficos avanzados para explorar los resultados en profundidad.

#### Pestana "Radar"

- Grafico tipo arana/radar que muestra el rendimiento de cada alternativa por vision.
- Cada eje del radar es una vision (V1-V8).
- Puedes seleccionar/deseleccionar alternativas para comparar.
- **Uso:** Identificar fortalezas y debilidades de cada alternativa.

#### Pestana "Heatmap"

- Mapa de calor con colores rojo-amarillo-verde.
- Filas = alternativas, Columnas = indicadores o visiones.
- **Verde** = buen rendimiento, **Rojo** = mal rendimiento.
- Activar "Agrupar por vision" para una vista resumida.
- **Uso:** Vision global rapida de todas las alternativas vs criterios.

#### Pestana "Barras Apiladas"

- Cada barra es una alternativa, dividida en segmentos de color por vision.
- Muestra cuanto contribuye cada vision al score total.
- **Uso:** Entender POR QUE una alternativa tiene mejor score.

#### Pestana "Waterfall"

- Grafico cascada para UNA alternativa seleccionada.
- Muestra la contribucion de cada vision al score, sumandose una a una.
- Barras verdes = contribucion positiva, rojas = negativa.
- **Uso:** Descomponer el score de una alternativa especifica.

#### Pestana "Coordenadas Paralelas"

- Cada linea vertical es un indicador.
- Cada linea de color es una alternativa.
- **Uso:** Comparar multiples alternativas en todos los indicadores simultaneamente.

---

### PAGINA 5: Comparacion de Metodos

**Que hace:** Ejecuta los 3 metodos (Suma Ponderada, TOPSIS, ELECTRE) y compara rankings.

**Pasos:**

1. Clic en **"Ejecutar Comparacion"**.
2. Revisa el grafico de lineas: si las lineas son paralelas, los metodos estan de acuerdo.
3. Revisa la tabla comparativa con rankings de cada metodo.
4. Revisa el **analisis de concordancia**:
   - **Spearman rho**: Correlacion entre rankings (-1 a 1). Mayor que 0.8 = buena concordancia.
   - **Kendall tau**: Otra medida de concordancia. Mayor que 0.6 = buena concordancia.

**Interpretacion:**
- Si los 3 metodos dan el mismo ranking → Alta confianza en la decision.
- Si difieren → Revisar los criterios y pesos, la decision es sensible al metodo.

---

### PAGINA 6: Sensibilidad

**Que hace:** Evalua que tan robusta es la decision ante cambios en los pesos.

#### Pestana "Sensibilidad OAT" (One-at-a-Time)

1. Ajustar **"Variacion de pesos (%)"**: Cuanto variar cada peso (default: 10%).
2. Seleccionar **metodo** (Suma Ponderada o TOPSIS).
3. Clic en **"Ejecutar Sensibilidad"**.
4. Seleccionar una alternativa para ver su grafico **Tornado**.

**Interpretar el Tornado:**
- Barras largas = el resultado es MUY sensible a ese criterio.
- Barras cortas = el criterio casi no afecta el resultado.
- Si la mejor alternativa cambia de posicion con variaciones pequenas → la decision es fragil.

#### Pestana "Monte Carlo"

1. Configurar:
   - **Numero de simulaciones**: 1000 (default). Mas simulaciones = mas precision.
   - **Variacion de pesos (%)**: 20% (default). Rango de variacion aleatoria.
   - **Distribucion**: `uniform` (igual probabilidad) o `triangular` (mas probable cerca del peso base).
2. Clic en **"Ejecutar Monte Carlo"**.

**Interpretar resultados:**
- **Box Plot**: Muestra la distribucion del score por alternativa. Cajas mas angostas = resultados mas estables.
- **Histograma de Rankings**: Muestra cuantas veces cada alternativa queda en cada posicion.
- **Tabla resumen**:
  - `mean_rank`: Ranking promedio (menor = mejor).
  - `pct_first`: % de veces que la alternativa queda 1ra.
  - `pct_top3`: % de veces que queda en el top 3.

**Ejemplo de interpretacion:**
```
Proponente A: mean_rank=1.3, pct_first=75%, pct_top3=100%
Proponente B: mean_rank=2.1, pct_first=20%, pct_top3=95%
```
→ Proponente A es la mejor opcion robusta (75% de las veces es 1ra).

---

### PAGINA 7: Reporte

**Que hace:** Genera documentos exportables con los resultados.

#### Exportar a PDF

1. Escribir el titulo del reporte.
2. Seleccionar las secciones a incluir (Resumen, Pesos, Resultados, Graficos, Sensibilidad, Comparacion).
3. Clic en **"Generar Reporte PDF"**.
4. Descargar el archivo PDF generado.

#### Exportar a Excel

1. Clic en **"Exportar a Excel"**.
2. Se genera un archivo `AMC_Resultados.xlsx` con hojas:
   - Resultados (rankings)
   - Contribuciones (por criterio)
   - Valores (matriz original)
   - Comparacion Metodos (si fue ejecutada)
   - Monte Carlo (si fue ejecutado)

---

## 5. Flujo de trabajo recomendado

```
┌─────────────────────────────────────────────────────┐
│  1. PREPARAR DATOS                                   │
│     Llenar la hoja VALORES del Excel con datos       │
│     reales de cada alternativa                       │
├─────────────────────────────────────────────────────┤
│  2. LANZAR LA APP                                    │
│     streamlit run app/main.py                        │
├─────────────────────────────────────────────────────┤
│  3. VERIFICAR DATOS (Pagina 1 - Inicio)              │
│     Confirmar que los datos se cargaron bien          │
├─────────────────────────────────────────────────────┤
│  4. AJUSTAR PESOS (Pagina 2 - Pesos)                │
│     Verificar CR < 0.10                              │
│     Ajustar pesos de visiones si es necesario        │
├─────────────────────────────────────────────────────┤
│  5. CALCULAR RESULTADOS (Pagina 3)                   │
│     Obtener el ranking con Suma Ponderada            │
├─────────────────────────────────────────────────────┤
│  6. EXPLORAR VISUALMENTE (Pagina 4)                  │
│     Radar, Heatmap, Waterfall para entender          │
│     por que gana cada alternativa                    │
├─────────────────────────────────────────────────────┤
│  7. VALIDAR CON OTROS METODOS (Pagina 5)             │
│     Comparar Suma Ponderada vs TOPSIS vs ELECTRE     │
├─────────────────────────────────────────────────────┤
│  8. VERIFICAR ROBUSTEZ (Pagina 6)                    │
│     Monte Carlo con 1000 simulaciones                │
│     Tornado para identificar criterios sensibles     │
├─────────────────────────────────────────────────────┤
│  9. GENERAR REPORTE (Pagina 7)                       │
│     Exportar PDF para presentar resultados           │
└─────────────────────────────────────────────────────┘
```

---

## 6. Estructura de archivos del proyecto

```
AMC/
│
├── TU_ARCHIVO_AMC.xlsx/.xlsm   ← Archivo Excel provisto por el usuario
├── AMC_Modelo.xlsx             ← Plantilla opcional generada por `crear_modelo.py`
├── requirements.txt              ← Lista de dependencias Python
├── GUIA_AMC.md                   ← Este documento
│
└── app/                          ← Codigo fuente de la aplicacion
    ├── __init__.py
    ├── main.py                   ← Dashboard Streamlit (punto de entrada)
    ├── data_loader.py            ← Lee datos del Excel
    ├── ahp.py                    ← Motor AHP y verificacion de consistencia
    ├── mcda_methods.py           ← Suma Ponderada, TOPSIS, ELECTRE I
    ├── normalization.py          ← 5 metodos de normalizacion
    ├── sensitivity.py            ← Sensibilidad OAT y Monte Carlo
    ├── charts.py                 ← 13 tipos de graficos Plotly
    └── report_generator.py       ← Generador de reportes PDF
```

### Que hace cada modulo

| Archivo | Funcion | Funciones principales |
|---------|---------|----------------------|
| `data_loader.py` | Lee el Excel y extrae todos los datos | `load_from_excel()`, `get_decision_matrix()`, `get_weights_from_data()` |
| `ahp.py` | Calcula pesos AHP y verifica consistencia | `consistency_ratio()`, `compute_weights()`, `hierarchical_weights()` |
| `normalization.py` | Normaliza valores para hacerlos comparables | `normalize_matrix()` con metodos: min_max, z_score, max, sum, vector |
| `mcda_methods.py` | Ejecuta los 3 metodos de decision | `weighted_sum()`, `topsis()`, `electre_i()`, `compare_methods()` |
| `sensitivity.py` | Analiza robustez de la decision | `one_at_a_time_sensitivity()`, `monte_carlo_simulation()` |
| `charts.py` | Genera graficos interactivos | 13 funciones: `radar_chart()`, `heatmap_chart()`, `tornado_chart()`, etc. |
| `report_generator.py` | Exporta resultados a PDF | `generate_report()` |

---

## 7. Glosario de terminos

| Termino | Significado |
|---------|-------------|
| **Alternativa** | Cada opcion que se esta evaluando (ej: Proponente A, B, C...) |
| **Criterio/Indicador** | Cada aspecto por el que se evaluan las alternativas (ej: costo, calidad) |
| **Vision** | Grupo de objetivos estrategicos (nivel superior de la jerarquia) |
| **Peso** | Importancia relativa de un criterio (de 0 a 1, suman 1) |
| **Normalizacion** | Proceso de hacer comparables valores en diferentes escalas |
| **AHP** | Analytic Hierarchy Process - metodo para derivar pesos de comparaciones |
| **CR** | Consistency Ratio - mide si las comparaciones AHP son logicas (debe ser < 0.10) |
| **TOPSIS** | Metodo que mide distancia al mejor y peor escenario posible |
| **ELECTRE** | Metodo que identifica relaciones de superacion entre alternativas |
| **SUMA** | Indicador de beneficio (mas es mejor) |
| **RESTA** | Indicador de costo (menos es mejor) |
| **Score** | Puntuacion final de una alternativa (0 a 1, mayor = mejor) |
| **Ranking** | Posicion de una alternativa (1 = mejor) |
| **Sensibilidad OAT** | Variar un peso a la vez para ver como cambia el resultado |
| **Monte Carlo** | Variar todos los pesos aleatoriamente miles de veces |
| **Tornado** | Grafico que muestra que criterios mas afectan el resultado |

---

## 8. Preguntas frecuentes

**P: Los resultados muestran todo en cero.**
R: La hoja VALORES del Excel no tiene datos cargados. Ingresa los valores reales de cada alternativa para cada indicador.

**P: El CR sale mayor a 0.10 (inconsistente).**
R: Revisa las comparaciones pareadas en la hoja Priorizacion del Excel. Asegurate de que si A es 3 veces mas importante que B, y B es 2 veces mas importante que C, entonces A deberia ser ~6 veces mas importante que C.

**P: TOPSIS y Suma Ponderada dan rankings diferentes.**
R: Es normal que difieran ligeramente. Si difieren mucho, la decision es sensible al metodo. Usa Monte Carlo para verificar robustez.

**P: Como cambio los indicadores o alternativas?**
R: Modifica las hojas INDICADORES, ALTERNATIVAS y VALORES en el Excel original y recarga la app.

**P: Puedo usar otro archivo Excel?**
R: Si, usa el boton "Cargar archivo Excel" en la barra lateral. El archivo debe tener la misma estructura de hojas.

---

## 9. Soporte

Para dudas o mejoras, contactar al equipo de desarrollo.

Herramienta desarrollada con: Python, Streamlit, Plotly, OpenPyXL, SciPy, ReportLab.
