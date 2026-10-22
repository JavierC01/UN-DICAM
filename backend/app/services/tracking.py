import cv2
import numpy as np

from app.schemas.common import Point
from app.schemas.tracking import MeshRequest, MeshResponse, TrackingValidationResponse


class TrackingServiceError(RuntimeError):
    pass


class TrackingService:
    def validate(self, payload: MeshRequest) -> TrackingValidationResponse:
        area = self._polygon_area(payload.puntos)
        min_area = payload.frame_width * payload.frame_height * 0.005
        valid = len(payload.puntos) >= 3 and area >= min_area
        message = "Poligono valido" if valid else "El poligono debe tener minimo 3 puntos y cubrir mas area"
        return TrackingValidationResponse(valid=valid, area_px=area, message=message)

    def build_mesh(self, payload: MeshRequest) -> MeshResponse:
        validation = self.validate(payload)
        if not validation.valid:
            raise TrackingServiceError(validation.message)
        mask = self._build_mask(payload.frame_width, payload.frame_height, payload.puntos)
        nodes = self._distribute_nodes(mask, payload.filas, payload.columnas)
        return MeshResponse(
            nodos=nodes,
            poligono=payload.puntos,
            area_px=validation.area_px,
            filas=payload.filas,
            columnas=payload.columnas,
        )

    def _build_mask(self, width: int, height: int, points: list[Point]) -> np.ndarray:
        polygon = np.array([[(int(p.x), int(p.y)) for p in points]], dtype=np.int32)
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, polygon, 255)
        return mask

    def _distribute_nodes(self, mask: np.ndarray, filas: int, columnas: int) -> list[Point]:
        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            raise TrackingServiceError("La mascara del poligono esta vacia")

        x_values = np.linspace(xs.min(), xs.max(), columnas)
        y_values = np.linspace(ys.min(), ys.max(), filas)
        nodes: list[Point] = []

        for y in y_values:
            for x in x_values:
                node_x, node_y = self._nearest_mask_pixel(mask, int(round(x)), int(round(y)))
                nodes.append(Point(x=float(node_x), y=float(node_y)))
        return nodes

    def _nearest_mask_pixel(self, mask: np.ndarray, x: int, y: int) -> tuple[int, int]:
        if 0 <= y < mask.shape[0] and 0 <= x < mask.shape[1] and mask[y, x] > 0:
            return x, y

        ys, xs = np.where(mask > 0)
        distance = (xs - x) ** 2 + (ys - y) ** 2
        idx = int(np.argmin(distance))
        return int(xs[idx]), int(ys[idx])

    def _polygon_area(self, points: list[Point]) -> float:
        x = np.array([p.x for p in points])
        y = np.array([p.y for p in points])
        return float(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))
