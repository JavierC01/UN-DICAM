from dataclasses import dataclass

# La malla de rastreo es una grilla filas x columnas ordenada por filas (ver Rastreo._distribuir_nodos), p. ej. 3x3:
#   0 1 2
#   3 4 5
#   6 7 8


@dataclass(frozen=True)
class CampoDeformacion:
    eps_xx: list[list[float]]
    eps_yy: list[list[float]]
    eps_xy: list[list[float]]
    eps_xx_medio: float
    eps_yy_medio: float
    eps_xy_medio: float


def _deformacion_cuadrante(
    esquinas: tuple[int, int, int, int],
    nodos_mm: list[dict[str, float]],
    desplazamientos_mm: list[tuple[float, float]],
) -> tuple[float, float, float]:
    sup_izq, sup_der, inf_izq, inf_der = esquinas

    x_izq = (nodos_mm[sup_izq]["x"] + nodos_mm[inf_izq]["x"]) / 2
    x_der = (nodos_mm[sup_der]["x"] + nodos_mm[inf_der]["x"]) / 2
    y_sup = (nodos_mm[sup_izq]["y"] + nodos_mm[sup_der]["y"]) / 2
    y_inf = (nodos_mm[inf_izq]["y"] + nodos_mm[inf_der]["y"]) / 2

    dx = x_der - x_izq
    dy = y_inf - y_sup
    if dx == 0 or dy == 0:
        return 0.0, 0.0, 0.0

    u_izq = (desplazamientos_mm[sup_izq][0] + desplazamientos_mm[inf_izq][0]) / 2
    u_der = (desplazamientos_mm[sup_der][0] + desplazamientos_mm[inf_der][0]) / 2
    u_sup = (desplazamientos_mm[sup_izq][0] + desplazamientos_mm[sup_der][0]) / 2
    u_inf = (desplazamientos_mm[inf_izq][0] + desplazamientos_mm[inf_der][0]) / 2

    v_izq = (desplazamientos_mm[sup_izq][1] + desplazamientos_mm[inf_izq][1]) / 2
    v_der = (desplazamientos_mm[sup_der][1] + desplazamientos_mm[inf_der][1]) / 2
    v_sup = (desplazamientos_mm[sup_izq][1] + desplazamientos_mm[sup_der][1]) / 2
    v_inf = (desplazamientos_mm[inf_izq][1] + desplazamientos_mm[inf_der][1]) / 2

    eps_xx = (u_der - u_izq) / dx
    eps_yy = (v_inf - v_sup) / dy
    eps_xy = 0.5 * ((u_inf - u_sup) / dy + (v_der - v_izq) / dx)
    return eps_xx, eps_yy, eps_xy


def calcular_deformaciones(
    nodos_mm: list[dict[str, float]], desplazamientos_mm: list[tuple[float, float]], columnas: int = 3
) -> CampoDeformacion:
    """Calcula la deformacion ingenieril (exx, eyy, exy) en cada celda de la grilla de nodos

    (filas-1 x columnas-1 celdas), usando diferencias finitas entre los 4 nodos de cada celda
    (aproximacion de extensometro virtual, sin necesitar un campo denso por pixel).
    """
    filas = len(nodos_mm) // columnas if columnas > 0 else 0
    if filas < 2 or columnas < 2 or len(nodos_mm) != filas * columnas or len(desplazamientos_mm) != len(nodos_mm):
        raise ValueError("Se requiere una grilla de nodos de al menos 2x2 organizada por filas")

    valores = []
    for f in range(filas - 1):
        fila = []
        for c in range(columnas - 1):
            sup_izq = f * columnas + c
            inf_izq = sup_izq + columnas
            esquinas = (sup_izq, sup_izq + 1, inf_izq, inf_izq + 1)
            fila.append(_deformacion_cuadrante(esquinas, nodos_mm, desplazamientos_mm))
        valores.append(fila)
    celdas = [v for fila in valores for v in fila]

    return CampoDeformacion(
        eps_xx=[[v[0] for v in fila] for fila in valores],
        eps_yy=[[v[1] for v in fila] for fila in valores],
        eps_xy=[[v[2] for v in fila] for fila in valores],
        eps_xx_medio=sum(v[0] for v in celdas) / len(celdas),
        eps_yy_medio=sum(v[1] for v in celdas) / len(celdas),
        eps_xy_medio=sum(v[2] for v in celdas) / len(celdas),
    )
