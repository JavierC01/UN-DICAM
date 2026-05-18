from dataclasses import dataclass, field


@dataclass
class AnalysisAccumulator:
    curva_desplaz_carga: dict[str, list[float]] = field(default_factory=lambda: {"x": [], "y": []})
    curva_esfuerzo_strain: dict[str, list[float]] = field(default_factory=lambda: {"x": [], "y": []})

    def process_frame(self, carga_n: float, desplazamiento_mm: float, strain: float, esfuerzo_mpa: float) -> dict:
        self.curva_desplaz_carga["x"].append(carga_n)
        self.curva_desplaz_carga["y"].append(desplazamiento_mm)
        self.curva_esfuerzo_strain["x"].append(strain)
        self.curva_esfuerzo_strain["y"].append(esfuerzo_mpa)
        return {
            "curva_desplaz_carga": self.curva_desplaz_carga,
            "curva_esfuerzo_strain": self.curva_esfuerzo_strain,
        }
