from app.schemas.specimen import SpecimenConfigRequest, SpecimenConfigResponse


class SpecimenServiceError(RuntimeError):
    pass


class SpecimenService:
    def configure(self, payload: SpecimenConfigRequest) -> SpecimenConfigResponse:
        if payload.long_calibracion_mm == 0:
            raise SpecimenServiceError("La longitud real de calibracion no puede ser cero")

        px_por_mm = payload.long_calibracion_px / payload.long_calibracion_mm
        mm_por_px = 1 / px_por_mm
        area_mm2 = payload.ancho_mm * payload.espesor_mm

        return SpecimenConfigResponse(
            px_por_mm=px_por_mm,
            mm_por_px=mm_por_px,
            area_mm2=area_mm2,
            confirmado=True,
        )
