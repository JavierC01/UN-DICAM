from dataclasses import dataclass

# La malla de rastreo siempre tiene 9 nodos en una grilla 3x3 (ver Rastreo._distribuir_9_nodos):
#   0 1 2
#   3 4 5
#   6 7 8
_CUADRANTES = ((0, 1, 3, 4), (1, 2, 4, 5), (3, 4, 6, 7), (4, 5, 7, 8))


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
    nodos_mm: list[dict[str, float]], desplazamientos_mm: list[tuple[float, float]]
) -> CampoDeformacion:
    """Calcula la deformacion ingenieril (exx, eyy, exy) en los 4 cuadrantes de la grilla 3x3

    de nodos, usando diferencias finitas entre los nodos que forman cada cuadrante
    (aproximacion de extensometro virtual, sin necesitar un campo denso por pixel).
    """
    if len(nodos_mm) != 9 or len(desplazamientos_mm) != 9:
        raise ValueError("Se requieren exactamente 9 nodos organizados en una grilla 3x3")

    valores = [_deformacion_cuadrante(cuadrante, nodos_mm, desplazamientos_mm) for cuadrante in _CUADRANTES]
    eps_xx = [[valores[0][0], valores[1][0]], [valores[2][0], valores[3][0]]]
    eps_yy = [[valores[0][1], valores[1][1]], [valores[2][1], valores[3][1]]]
    eps_xy = [[valores[0][2], valores[1][2]], [valores[2][2], valores[3][2]]]

    return CampoDeformacion(
        eps_xx=eps_xx,
        eps_yy=eps_yy,
        eps_xy=eps_xy,
        eps_xx_medio=sum(v[0] for v in valores) / len(valores),
        eps_yy_medio=sum(v[1] for v in valores) / len(valores),
        eps_xy_medio=sum(v[2] for v in valores) / len(valores),
    )
