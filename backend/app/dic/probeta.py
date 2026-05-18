from dataclasses import dataclass


@dataclass(frozen=True)
class MedidasProbeta:
    long_calibracion_px: float
    long_calibracion_mm: float
    ancho_mm: float
    espesor_mm: float
    long_calibre_mm: float


class Probeta:
    def __init__(self, medidas: MedidasProbeta) -> None:
        self.medidas = medidas
        self.px_por_mm = medidas.long_calibracion_px / medidas.long_calibracion_mm
        self.mm_por_px = 1 / self.px_por_mm
        self.area_mm2 = medidas.ancho_mm * medidas.espesor_mm

    def convertir_desplazamiento(self, desplazamiento_px: float) -> float:
        return desplazamiento_px * self.mm_por_px

    def calcular_esfuerzo(self, carga_n: float) -> float:
        return carga_n / self.area_mm2

    def preparar_datos_analisis(self, u_px: float, v_px: float, eps_xx: float, eps_yy: float, eps_xy: float, carga_n: float) -> dict:
        return {
            "u_mm": self.convertir_desplazamiento(u_px),
            "v_mm": self.convertir_desplazamiento(v_px),
            "eps_xx": eps_xx,
            "eps_yy": eps_yy,
            "eps_xy": eps_xy,
            "carga_n": carga_n,
            "esfuerzo_mpa": self.calcular_esfuerzo(carga_n),
        }
