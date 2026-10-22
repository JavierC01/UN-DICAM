from dataclasses import dataclass

import numpy as np

from app.dic.displacement import ResultadoNodo, rastrear_malla
from app.dic.strain import CampoDeformacion, calcular_deformaciones


@dataclass(frozen=True)
class ResultadoFrame:
    nodos: list[ResultadoNodo]
    coef_correlacion_medio: float
    campo: CampoDeformacion
    nodo_centro: ResultadoNodo
    u_mm_centro: float
    v_mm_centro: float


def procesar_par_frames(
    imagen_ref: np.ndarray,
    imagen_def: np.ndarray,
    nodos_ref_px: list[dict[str, float]],
    mm_por_px: float,
    subset_size: int,
    search_range: int,
    filas: int = 3,
    columnas: int = 3,
) -> ResultadoFrame:
    """Rastrea la malla de filas x columnas nodos entre dos frames y calcula el campo de deformacion resultante."""
    resultados = rastrear_malla(imagen_ref, imagen_def, nodos_ref_px, subset_size, search_range)

    nodos_mm = [{"x": nodo["x"] * mm_por_px, "y": nodo["y"] * mm_por_px} for nodo in nodos_ref_px]
    desplazamientos_mm = [(r.u_px * mm_por_px, r.v_px * mm_por_px) for r in resultados]
    campo = calcular_deformaciones(nodos_mm, desplazamientos_mm, columnas)

    centro = resultados[(filas // 2) * columnas + columnas // 2]
    return ResultadoFrame(
        nodos=resultados,
        coef_correlacion_medio=float(np.mean([r.coef_correlacion for r in resultados])),
        campo=campo,
        nodo_centro=centro,
        u_mm_centro=centro.u_px * mm_por_px,
        v_mm_centro=centro.v_px * mm_por_px,
    )
