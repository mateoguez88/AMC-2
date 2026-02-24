"""
AMC - Analisis Multicriterio Tool
Dashboard interactivo para evaluacion multicriterio con
Suma Ponderada, TOPSIS, ELECTRE I, AHP y Monte Carlo.
"""

__version__ = "1.1.0"

from app.data_loader import AMCData, load_from_excel
from app.mcda_methods import weighted_sum, topsis, electre_i
from app.ahp import consistency_ratio, AHPResult

__all__ = [
    "AMCData",
    "AHPResult",
    "load_from_excel",
    "weighted_sum",
    "topsis",
    "electre_i",
    "consistency_ratio",
]
