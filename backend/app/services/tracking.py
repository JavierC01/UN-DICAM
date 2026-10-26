from app.dic import rastreo
from app.dic.ensayos import obtener_ensayo
from app.dic.strain import localizar_punto
from app.schemas.common import Point
from app.schemas.tracking import MeshRequest, MeshResponse, TrackingValidationResponse


class TrackingServiceError(RuntimeError):
    pass


def _dicts(puntos: list[Point]) -> list[dict[str, float]]:
    return [p.model_dump() for p in puntos]


class TrackingService:
    def validate(self, payload: MeshRequest) -> TrackingValidationResponse:
        area = rastreo.area_poligono(_dicts(payload.puntos))
        min_area = payload.frame_width * payload.frame_height * 0.005
        valid = len(payload.puntos) >= 3 and area >= min_area
        message = "Poligono valido" if valid else "El poligono debe tener minimo 3 puntos y cubrir mas area"
        return TrackingValidationResponse(valid=valid, area_px=area, message=message)

    def build_mesh(self, payload: MeshRequest) -> MeshResponse:
        validation = self.validate(payload)
        if not validation.valid:
            raise TrackingServiceError(validation.message)
        try:
            malla = rastreo.construir_malla(
                payload.frame_width,
                payload.frame_height,
                _dicts(payload.puntos),
                payload.filas,
                payload.columnas,
                payload.subset_size,
            )
        except ValueError as exc:
            raise TrackingServiceError(str(exc)) from exc
        return MeshResponse(
            nodos=[Point(**n) for n in malla.nodos],
            validos=malla.validos,
            poligono=payload.puntos,
            area_px=validation.area_px,
            filas=payload.filas,
            columnas=payload.columnas,
            subset_size=payload.subset_size,
        )

    def validate_test_points(
        self,
        tipo_ensayo: str,
        puntos: list[Point],
        nodos: list[dict],
        validos: list[bool] | None,
        poligono: list[dict],
        ancho: int,
        alto: int,
    ) -> None:
        """Los puntos del extensometro virtual deben caer dentro de la malla triangulada para poder interpolarlos."""
        try:
            obtener_ensayo(tipo_ensayo).validar_puntos(_dicts(puntos))
        except ValueError as exc:
            raise TrackingServiceError(str(exc)) from exc
        mascara = rastreo.generar_mascara(ancho, alto, poligono)
        triangulos = rastreo.triangular(nodos, validos or [True] * len(nodos), mascara)
        fuera = [i + 1 for i, p in enumerate(puntos) if localizar_punto(p.model_dump(), nodos, triangulos) is None]
        if fuera:
            raise TrackingServiceError(
                f"Los puntos {', '.join(map(str, fuera))} quedan fuera de la malla de nodos validos; marcalos dentro de ella"
            )
