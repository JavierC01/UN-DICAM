from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Analisis:
    output_dir: str
    curva_desplaz_carga: dict[str, list[float]] = field(default_factory=lambda: {"x": [], "y": []})
    curva_esfuerzo_strain: dict[str, list[float]] = field(default_factory=lambda: {"x": [], "y": []})

    def __post_init__(self) -> None:
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def procesar_frame(self, datos: dict, frame_id: int) -> dict:
        self.curva_desplaz_carga["x"].append(float(datos["carga_n"]))
        self.curva_desplaz_carga["y"].append(float(datos["v_mm"]))
        self.curva_esfuerzo_strain["x"].append(float(datos["eps_yy"]))
        self.curva_esfuerzo_strain["y"].append(float(datos["esfuerzo_mpa"]))
        return {
            "frame_id": frame_id,
            "curva_desplaz_carga": self.curva_desplaz_carga,
            "curva_esfuerzo_strain": self.curva_esfuerzo_strain,
        }
