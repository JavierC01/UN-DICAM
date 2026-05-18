from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class MallaRastreo:
    nodos: list[dict[str, float]]
    poligono: list[dict[str, float]]
    area_px: float
    mascara: np.ndarray


class Rastreo:
    def __init__(self, frame_width: int, frame_height: int) -> None:
        self.frame_width = frame_width
        self.frame_height = frame_height

    def construir_malla(self, puntos: list[dict[str, float]]) -> MallaRastreo:
        area = self.area_poligono(puntos)
        mascara = self._generar_mascara(puntos)
        nodos = self._distribuir_9_nodos(mascara)
        return MallaRastreo(nodos=nodos, poligono=puntos, area_px=area, mascara=mascara)

    def _generar_mascara(self, puntos: list[dict[str, float]]) -> np.ndarray:
        polygon = np.array([[(int(p["x"]), int(p["y"])) for p in puntos]], dtype=np.int32)
        mask = np.zeros((self.frame_height, self.frame_width), dtype=np.uint8)
        cv2.fillPoly(mask, polygon, 255)
        return mask

    def _distribuir_9_nodos(self, mascara: np.ndarray) -> list[dict[str, float]]:
        ys, xs = np.where(mascara > 0)
        if len(xs) == 0:
            raise ValueError("La mascara del poligono esta vacia")
        nodes: list[dict[str, float]] = []
        for y in np.linspace(ys.min(), ys.max(), 3):
            for x in np.linspace(xs.min(), xs.max(), 3):
                px, py = self._pixel_mas_cercano(mascara, int(round(x)), int(round(y)))
                nodes.append({"x": float(px), "y": float(py)})
        return nodes

    def _pixel_mas_cercano(self, mascara: np.ndarray, x: int, y: int) -> tuple[int, int]:
        if 0 <= y < mascara.shape[0] and 0 <= x < mascara.shape[1] and mascara[y, x] > 0:
            return x, y
        ys, xs = np.where(mascara > 0)
        idx = int(np.argmin((xs - x) ** 2 + (ys - y) ** 2))
        return int(xs[idx]), int(ys[idx])

    @staticmethod
    def area_poligono(puntos: list[dict[str, float]]) -> float:
        x = np.array([p["x"] for p in puntos])
        y = np.array([p["y"] for p in puntos])
        return float(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))
